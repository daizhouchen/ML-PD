"""Nested, subject-separated cross-validation with auditable out-of-fold summaries."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, classification_report,
                             confusion_matrix, f1_score, roc_auc_score, roc_curve)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, StratifiedGroupKFold

from . import __version__
from .data import DataError, load_dataset
from .models import MODEL_NAMES, model_spec


def make_splits(y, groups, n_splits, seed):
    if not isinstance(n_splits, int) or n_splits < 2:
        raise DataError("Use at least two folds.")
    for label in np.unique(y):
        if len(np.unique(groups[y == label])) < n_splits:
            raise DataError("Too few independent subjects per class for this fold count. Reduce folds or provide more subjects.")
    repeated = len(np.unique(groups)) < len(groups)
    cv = (StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed) if repeated
          else StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed))
    splits = list(cv.split(np.zeros(len(y)), y, groups if repeated else None))
    for train, test in splits:
        if set(groups[train]) & set(groups[test]):
            raise DataError("Subject overlap detected; evaluation cancelled.")
        if set(y[train]) != set(y) or set(y[test]) != set(y):
            raise DataError("A grouped fold is missing a class. Reduce folds or revise the prespecified cohort/split design.")
    return splits


def response_scores(estimator, X, n_classes):
    if not np.array_equal(estimator.classes_, np.arange(n_classes)):
        raise DataError("Unexpected estimator class order.")
    if hasattr(estimator, "predict_proba"):
        return estimator.predict_proba(X)
    scores = estimator.decision_function(X)
    return np.column_stack([-scores, scores]) if scores.ndim == 1 else scores


def compute_metrics(y, prediction, scores, n_classes):
    aucs = [roc_auc_score((y == label).astype(int), scores[:, label]) for label in range(n_classes)]
    return {"balanced_accuracy": float(balanced_accuracy_score(y, prediction)),
            "macro_f1": float(f1_score(y, prediction, average="macro", zero_division=0)),
            "accuracy": float(accuracy_score(y, prediction)), "macro_ovr_auc": float(np.mean(aucs))}


def _split_hash(groups):
    # Hash the sorted membership set, never expose actual subject IDs in public summaries.
    return hashlib.sha256("\n".join(sorted(set(groups))).encode()).hexdigest()


def evaluate_task(data, models, outer_folds, inner_folds, seed, jobs, progress=print):
    outer = make_splits(data.y, data.groups, outer_folds, seed)
    # Preflight all nested folds before fitting any model.
    inner = [make_splits(data.y[train], data.groups[train], inner_folds, seed + fold + 1)
             for fold, (train, _) in enumerate(outer)]
    n_classes = len(data.classes)
    results, feature_rows, assignments = [], [], []
    for fold, (train, test) in enumerate(outer):
        assignments.extend({"sample_id": data.sample_ids[i], "subject_id": data.groups[i], "outer_fold": fold + 1}
                           for i in test)
    for name in models:
        progress(f"  {MODEL_NAMES[name]}: {outer_folds} outer folds × {inner_folds} inner folds")
        folds, selections, curves = [], Counter(), {label: [] for label in range(n_classes)}
        predictions = np.full(len(data.y), -1, dtype=int)
        for fold, (train, test) in enumerate(outer):
            pipeline, grid = model_spec(name, seed + fold)
            search = GridSearchCV(pipeline, grid, scoring="balanced_accuracy", cv=inner[fold],
                                  n_jobs=jobs, refit=True, error_score="raise", return_train_score=False)
            search.fit(data.X.iloc[train], data.y[train])
            fitted = search.best_estimator_
            predicted = fitted.predict(data.X.iloc[test])
            predictions[test] = predicted
            scores = response_scores(fitted, data.X.iloc[test], n_classes)
            metrics = compute_metrics(data.y[test], predicted, scores, n_classes)
            names = fitted.named_steps["filter"].get_feature_names_out()
            selector = fitted.named_steps["select"]
            if name != "dummy":
                names = names[selector.support_]
                selections.update(names.tolist())
            folds.append({"fold": fold + 1, "train_samples": len(train), "test_samples": len(test),
                          "train_subjects": len(np.unique(data.groups[train])), "test_subjects": len(np.unique(data.groups[test])),
                          "train_membership_sha256": _split_hash(data.groups[train]),
                          "test_membership_sha256": _split_hash(data.groups[test]),
                          "best_params": search.best_params_, "inner_balanced_accuracy": float(search.best_score_),
                          "selected_features": len(names) if name != "dummy" else None, **metrics})
            for label in range(n_classes):
                fpr, tpr, _ = roc_curve((data.y[test] == label).astype(int), scores[:, label])
                interpolated = np.interp(np.linspace(0, 1, 101), fpr, tpr)
                interpolated[0], interpolated[-1] = 0, 1
                curves[label].append(interpolated)
        if (predictions < 0).any():
            raise DataError("Incomplete out-of-fold coverage.")
        summary = {key: {"mean": float(np.mean([f[key] for f in folds])),
                         "std": float(np.std([f[key] for f in folds], ddof=1))}
                   for key in ("balanced_accuracy", "macro_f1", "accuracy", "macro_ovr_auc")}
        features = [{"feature": str(feature), "selected_folds": selections[feature],
                     "frequency": selections[feature] / outer_folds} for feature in data.X.columns]
        features.sort(key=lambda item: (-item["frequency"], item["feature"]))
        feature_rows.extend({"model": name, **entry} for entry in features if name != "dummy")
        results.append({"id": name, "name": MODEL_NAMES[name], "summary": summary, "folds": folds,
                        "confusion_matrix": confusion_matrix(data.y, predictions, labels=np.arange(n_classes)).tolist(),
                        "classification_report": classification_report(data.y, predictions, labels=np.arange(n_classes),
                                                                       target_names=data.classes, output_dict=True, zero_division=0),
                        "roc": [{"class": data.classes[label], "fpr": np.linspace(0, 1, 101).tolist(),
                                 "mean_tpr": np.mean(curves[label], axis=0).tolist()} for label in range(n_classes)],
                        "feature_stability": features if name != "dummy" else []})
    return results, feature_rows, assignments


def run_experiment(csv_path, schema_path, output, *, tasks, models, outer_folds=5, inner_folds=3,
                   seed=2026, jobs=1, progress=print):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise DataError("Output directory is not empty; use a new run directory to avoid overwriting results.")
    if not tasks or len(set(tasks)) != len(tasks) or not models or len(set(models)) != len(models):
        raise DataError("Select unique, non-empty task and model lists.")
    if set(models) - set(MODEL_NAMES):
        raise DataError("Unknown model in model list.")
    if jobs == 0:
        raise DataError("jobs cannot be zero.")
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8-sig"))
    datasets = {task: load_dataset(csv_path, schema, task) for task in tasks}
    # Validate every task's split design up front, not halfway into an expensive run.
    for data in datasets.values():
        for fold, (train, _) in enumerate(make_splits(data.y, data.groups, outer_folds, seed)):
            make_splits(data.y[train], data.groups[train], inner_folds, seed + fold + 1)
    output.mkdir(parents=True, exist_ok=True)
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip())
    except (subprocess.SubprocessError, FileNotFoundError):
        commit, dirty = None, None
    report = {"format_version": 1, "package_version": __version__,
              "created_at": datetime.now(timezone.utc).isoformat(), "data_kind": schema["data_kind"],
              "data_sha256": next(iter(datasets.values())).digest,
              "schema_sha256": hashlib.sha256(Path(schema_path).read_bytes()).hexdigest(),
              "git_commit": commit, "working_tree_dirty": dirty,
              "runtime": {"python": platform.python_version(), **{package: importlib.metadata.version(package)
                          for package in ("numpy", "pandas", "scikit-learn", "xgboost", "matplotlib")}},
              "config": {"tasks": tasks, "models": models, "outer_folds": outer_folds,
                         "inner_folds": inner_folds, "seed": seed, "jobs": jobs,
                         "selection": "Training-only filter → median imputation → scaling → RFE; count and model params searched in inner folds",
                         "primary_metric": "balanced_accuracy"},
              "interpretation": ["Fold standard deviations describe variation; they are not confidence intervals.",
                                 "Model comparisons are descriptive, not a claim of statistical superiority.",
                                 "ROC curves average per-fold OVR curves; SVM margins are not calibrated probabilities.",
                                 "Cross-sectional class prediction is not disease progression prediction or clinical validation."], "tasks": []}
    all_metrics, all_features, all_assignments = [], [], []
    for task, data in datasets.items():
        progress(f"Task {task}: {len(data.y)} samples / {len(np.unique(data.groups))} subjects")
        result, features, assignments = evaluate_task(data, models, outer_folds, inner_folds, seed, jobs, progress)
        report["tasks"].append({"id": task, "classes": data.classes, "samples": len(data.y),
                                "subjects": len(np.unique(data.groups)), "features": data.X.shape[1],
                                "missing_fraction": float(data.X.isna().to_numpy().mean()),
                                "class_counts": {label: int((data.y == i).sum()) for i, label in enumerate(data.classes)},
                                "notes": data.notes, "models": result})
        for model in result:
            all_metrics.extend({"task": task, "model": model["id"], **{k: v for k, v in fold.items()
                                if k not in {"best_params", "train_membership_sha256", "test_membership_sha256"}}}
                               for fold in model["folds"])
        all_features.extend({"task": task, **row} for row in features)
        all_assignments.extend({"task": task, **row} for row in assignments)
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    pd.DataFrame(all_metrics).to_csv(output / "fold_metrics.csv", index=False)
    pd.DataFrame(all_features).to_csv(output / "feature_stability.csv", index=False)
    pd.DataFrame(all_assignments).to_csv(output / "split_assignments.csv", index=False)
    return report
