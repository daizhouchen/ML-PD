import json

import numpy as np
import pandas as pd
import pytest

from mlpd.data import DataError, TrainingFeatureFilter, load_dataset, make_demo


@pytest.fixture
def fixture(tmp_path):
    csv, schema = make_demo(tmp_path / "input", samples=90)
    return csv, json.loads(schema.read_text(encoding="utf-8"))


def test_contract_and_pairwise_relabeling(fixture):
    path, schema = fixture
    dataset = load_dataset(path, schema, "pd-prodromal")
    assert dataset.classes == ["Prodromal", "PD"]
    assert set(dataset.y) == {0, 1}
    assert dataset.X.shape[1] == 24
    assert not set(dataset.X.columns) & {"group", "subject_id", "sample_id"}


@pytest.mark.parametrize("mutation,match", [
    ("id_feature", "identifiers"), ("duplicate_id", "sample_id"),
    ("bad_label", "Unknown label"), ("infinity", "Infinite"),
    ("text_feature", "Non-numeric"), ("duplicate_subject_label", "conflicting"),
    ("duplicate_header", "duplicate column"), ("duplicate_row", "Duplicate feature"),
])
def test_rejects_unsafe_inputs(fixture, mutation, match):
    path, schema = fixture
    frame = pd.read_csv(path)
    if mutation == "id_feature":
        schema["feature_columns"].append("subject_id")
    elif mutation == "duplicate_id":
        frame.loc[1, "sample_id"] = frame.loc[0, "sample_id"]
    elif mutation == "bad_label":
        frame.loc[0, "group"] = "Unknown"
    elif mutation == "infinity":
        frame.loc[0, schema["feature_columns"][0]] = np.inf
    elif mutation == "text_feature":
        feature = schema["feature_columns"][0]
        frame[feature] = frame[feature].astype(object)
        frame.loc[0, feature] = "not measured"
    elif mutation == "duplicate_subject_label":
        other = frame.index[frame.group != frame.loc[0, "group"]][0]
        frame.loc[other, "subject_id"] = frame.loc[0, "subject_id"]
    elif mutation == "duplicate_row":
        frame.loc[1, schema["feature_columns"]] = frame.loc[0, schema["feature_columns"]]
    elif mutation == "duplicate_header":
        text = path.read_text()
        path.write_text(text.replace("synthetic_feature_02", "synthetic_feature_01", 1))
    if mutation != "duplicate_header":
        frame.to_csv(path, index=False)
    with pytest.raises(DataError, match=match):
        load_dataset(path, schema)


def test_training_filter_does_not_learn_from_validation():
    train = pd.DataFrame({"a": [1, 2, 3, 4], "b": [2, 1, 4, 3], "c": [np.nan, np.nan, np.nan, 2]})
    test = pd.DataFrame({"a": [np.nan], "b": [7], "c": [9]})
    fitted = TrainingFeatureFilter().fit(train)
    assert list(fitted.transform(test).columns) == ["a", "b"]
    assert fitted.transform(test).iloc[0].isna()["a"]
    with pytest.raises(DataError, match="schema/order"):
        fitted.transform(test[["b", "a", "c"]])


def test_demo_is_deterministic_and_non_destructive(tmp_path):
    first, _ = make_demo(tmp_path / "one")
    second, _ = make_demo(tmp_path / "two")
    assert first.read_bytes() == second.read_bytes()
    with pytest.raises(DataError, match="already exists"):
        make_demo(tmp_path / "one")
