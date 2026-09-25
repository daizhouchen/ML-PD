"""Explicit data contracts and training-only feature filtering."""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.datasets import make_classification
from sklearn.utils.validation import check_is_fitted

LABELS = ("Control", "Prodromal", "PD")
TASKS = {
    "three-class": LABELS,
    "pd-control": ("Control", "PD"),
    "prodromal-control": ("Control", "Prodromal"),
    "pd-prodromal": ("Prodromal", "PD"),
}


class DataError(ValueError):
    """Actionable input/configuration error."""


@dataclass
class Dataset:
    X: pd.DataFrame
    y: np.ndarray
    groups: np.ndarray
    sample_ids: np.ndarray
    classes: list[str]
    data_kind: str
    digest: str
    notes: list[str]


def load_dataset(path: str | Path, schema: dict, task: str = "three-class") -> Dataset:
    path = Path(path)
    if task not in TASKS:
        raise DataError(f"Unknown task: {task}")
    required = ("label_column", "sample_id_column", "subject_id_column", "feature_columns", "data_kind")
    if any(key not in schema for key in required):
        raise DataError("Schema requires label_column, sample_id_column, subject_id_column, feature_columns, data_kind.")
    features = schema["feature_columns"]
    if not isinstance(features, list) or len(features) < 2 or len(set(features)) != len(features):
        raise DataError("feature_columns must explicitly list at least two unique numeric features.")
    metadata = {schema[k] for k in required[:3]}
    if metadata.intersection(features):
        raise DataError("Label/sample/subject identifiers must never be model features.")
    if schema["data_kind"] not in {"synthetic", "private", "public"}:
        raise DataError("data_kind must be synthetic, private, or public.")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        header = next(csv.reader(handle), [])
    if len(header) != len(set(header)):
        raise DataError("CSV has duplicate column names; fix the export before training.")
    frame = pd.read_csv(path, dtype={column: "string" for column in metadata})
    missing = (set(features) | metadata) - set(frame.columns)
    if missing:
        raise DataError(f"CSV is missing {len(missing)} configured columns; check schema.")
    for column in metadata:
        if frame[column].isna().any() or frame[column].str.strip().eq("").any():
            raise DataError("Labels and identifiers must be present in every row.")
    ids = frame[schema["sample_id_column"]]
    if ids.duplicated().any():
        raise DataError("sample_id must be unique; repeated subjects need distinct sample IDs.")
    raw_labels = frame[schema["label_column"]]
    label_map = schema.get("label_mapping", {label: label for label in LABELS})
    mapped = raw_labels.map({str(k): v for k, v in label_map.items()})
    if mapped.isna().any() or not set(mapped).issubset(LABELS):
        raise DataError("Unknown label; map every input label to Control, Prodromal, or PD in schema.")
    full_subject_labels = pd.DataFrame({"subject": frame[schema["subject_id_column"]], "label": mapped}).groupby("subject")["label"].nunique()
    if full_subject_labels.gt(1).any():
        raise DataError("Subjects have conflicting class labels; resolve the cross-sectional cohort before choosing pairwise tasks.")
    selected = mapped.isin(TASKS[task])
    frame, mapped = frame.loc[selected], mapped.loc[selected]
    classes = list(TASKS[task])
    if set(mapped) != set(classes):
        raise DataError(f"Task {task} requires all of its configured classes.")
    try:
        X = frame[features].apply(pd.to_numeric, errors="raise").astype(float)
    except (ValueError, TypeError) as exc:
        raise DataError("Non-numeric feature value; use blank cells for missing observations.") from exc
    if np.isinf(X.to_numpy()).any():
        raise DataError("Infinite feature values are not allowed.")
    if X.isna().all(axis=1).any():
        raise DataError("A sample has no measured features; resolve it before training.")
    groups = frame[schema["subject_id_column"]].to_numpy(dtype=str)
    y = np.array([classes.index(label) for label in mapped], dtype=int)
    subject_labels = pd.DataFrame({"subject": groups, "label": y}).groupby("subject")["label"].nunique()
    if subject_labels.gt(1).any():
        raise DataError("Subjects have conflicting class labels. This workflow expects one cross-sectional label per subject; define a longitudinal protocol separately.")
    notes = []
    if len(np.unique(groups)) < len(groups):
        notes.append("Repeated samples are kept together by subject in every outer and inner split; metrics remain sample-weighted.")
    if X.duplicated().any():
        raise DataError("Duplicate feature rows detected; investigate duplicates before evaluation.")
    unused = set(frame.columns) - metadata - set(features)
    if unused:
        notes.append(f"{len(unused)} non-feature columns ignored by explicit schema.")
    return Dataset(X.reset_index(drop=True), y, groups, frame[schema["sample_id_column"]].to_numpy(dtype=str),
                   classes, schema["data_kind"], hashlib.sha256(path.read_bytes()).hexdigest(), notes)


class TrainingFeatureFilter(TransformerMixin, BaseEstimator):
    """Learn missingness/constant-column decisions solely from a training fold."""

    def __init__(self, max_missing=0.4):
        self.max_missing = max_missing

    def fit(self, X, y=None):
        if not 0 <= self.max_missing < 1:
            raise ValueError("max_missing must be in [0, 1).")
        frame = pd.DataFrame(X)
        self.n_features_in_ = frame.shape[1]
        self.feature_names_in_ = np.asarray(frame.columns, dtype=object)
        self.support_ = ((frame.isna().mean() <= self.max_missing) & (frame.nunique(dropna=True) > 1)).to_numpy()
        if self.support_.sum() < 2:
            raise DataError("A training fold has fewer than two usable features after missingness/constant filtering.")
        return self

    def transform(self, X):
        check_is_fitted(self, "support_")
        frame = pd.DataFrame(X)
        if frame.shape[1] != self.n_features_in_ or not np.array_equal(np.asarray(frame.columns), self.feature_names_in_):
            raise DataError("Feature schema/order changed between fitting and transformation.")
        return frame.iloc[:, self.support_]

    def get_feature_names_out(self, input_features=None):
        check_is_fitted(self, "support_")
        return self.feature_names_in_[self.support_]


def make_demo(directory: str | Path, seed: int = 2026, samples: int = 180) -> tuple[Path, Path]:
    """Synthetic numeric benchmark; never represents patients or real metabolite abundances."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    paths = directory / "synthetic.csv", directory / "schema.json"
    if any(p.exists() for p in paths):
        raise DataError("Demo output already exists; choose a new directory to preserve reproducibility.")
    if samples < 60:
        raise DataError("Use at least 60 synthetic samples.")
    X, y = make_classification(n_samples=samples, n_features=24, n_informative=8,
                               n_redundant=6, n_classes=3, n_clusters_per_class=1,
                               class_sep=0.8, flip_y=0.06, random_state=seed)
    rng = np.random.default_rng(seed)
    X[rng.random(X.shape) < 0.06] = np.nan
    features = [f"synthetic_feature_{i+1:02d}" for i in range(X.shape[1])]
    frame = pd.DataFrame(X, columns=features)
    frame.insert(0, "group", [LABELS[i] for i in y])
    frame.insert(0, "subject_id", [f"SIM-{i:04d}" for i in range(samples)])
    frame.insert(0, "sample_id", [f"SIM-{i:04d}-1" for i in range(samples)])
    frame.to_csv(paths[0], index=False)
    schema = {"label_column": "group", "sample_id_column": "sample_id", "subject_id_column": "subject_id",
              "feature_columns": features, "data_kind": "synthetic", "seed": seed,
              "description": "Generated numerical classification fixture. No patient data, metabolite identities, or clinical interpretation."}
    paths[1].write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    return paths
