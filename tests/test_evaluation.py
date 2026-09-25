import json

import numpy as np
import pandas as pd
import pytest

from mlpd.data import DataError, TrainingFeatureFilter, load_dataset, make_demo
from mlpd.evaluate import evaluate_task, make_splits, run_experiment
from mlpd.reporting import publish_demo


def test_grouped_splits_preserve_subjects_in_both_loops():
    y = np.repeat(np.repeat([0, 1, 2], 12), 2)
    groups = np.repeat([f"subject-{i}" for i in range(36)], 2)
    tests = []
    for fold, (train, test) in enumerate(make_splits(y, groups, 3, 11)):
        assert not set(groups[train]) & set(groups[test])
        tests.extend(test)
        for inner_train, inner_test in make_splits(y[train], groups[train], 2, fold):
            assert not set(groups[train][inner_train]) & set(groups[train][inner_test])
    assert sorted(tests) == list(range(len(y)))


def test_insufficient_subjects_fail_before_fitting():
    with pytest.raises(DataError, match="Too few"):
        make_splits(np.array([0, 0, 1, 1]), np.array(["a", "b", "c", "d"]), 3, 1)


def test_every_preprocessing_fit_is_a_prescribed_training_partition(tmp_path, monkeypatch):
    path, schema_path = make_demo(tmp_path / "input", samples=60)
    data = load_dataset(path, json.loads(schema_path.read_text()))
    allowed, fits = set(), []
    for fold, (train, _) in enumerate(make_splits(data.y, data.groups, 3, 2026)):
        allowed.add(frozenset(train))
        for inner_train, _ in make_splits(data.y[train], data.groups[train], 2, 2026 + fold + 1):
            allowed.add(frozenset(train[inner_train]))
    original = TrainingFeatureFilter.fit

    def spy(self, X, y=None):
        fits.append(frozenset(X.index))
        return original(self, X, y)

    monkeypatch.setattr(TrainingFeatureFilter, "fit", spy)
    result, _, assignments = evaluate_task(data, ["dummy"], 3, 2, 2026, 1, lambda _: None)
    assert len(fits) == 9
    assert all(partition in allowed for partition in fits)
    assert len(assignments) == len(data.y)
    assert sum(map(sum, result[0]["confusion_matrix"])) == len(data.y)


def test_real_nested_run_and_public_export_gate(tmp_path):
    path, schema = make_demo(tmp_path / "input", samples=60)
    report = run_experiment(path, schema, tmp_path / "run", tasks=["pd-control"],
                            models=["dummy", "logistic"], outer_folds=3, inner_folds=2, progress=lambda _: None)
    task = report["tasks"][0]
    assert len(task["models"][1]["feature_stability"]) == 24
    assert all(0 <= entry["frequency"] <= 1 for entry in task["models"][1]["feature_stability"])
    assert all(0 <= stat["mean"] <= 1 for model in task["models"] for stat in model["summary"].values())
    assignments = pd.read_csv(tmp_path / "run/split_assignments.csv")
    assert assignments.groupby("sample_id").size().eq(1).all()
    assert task["models"][1]["folds"][0]["best_params"]["select__n_features_to_select"] in (0.5, 1.0)
    # The automatic publication path must reject private data before it creates output.
    report["data_kind"] = "private"
    private = tmp_path / "private.json"
    private.write_text(json.dumps(report))
    with pytest.raises(DataError, match="only accepts synthetic"):
        publish_demo(private, tmp_path / "site")
    assert not (tmp_path / "site").exists()


def test_output_is_not_silently_overwritten(tmp_path):
    path, schema = make_demo(tmp_path / "input", samples=60)
    out = tmp_path / "run"
    out.mkdir()
    (out / "keep.txt").write_text("existing run")
    with pytest.raises(DataError, match="not empty"):
        run_experiment(path, schema, out, tasks=["three-class"], models=["dummy"])
    assert (out / "keep.txt").read_text() == "existing run"
