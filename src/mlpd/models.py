"""Each search refits preprocessing and RFE inside its training split."""
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_selection import RFE
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from .data import TrainingFeatureFilter, DataError

MODEL_NAMES = {
    "dummy": "Prior baseline", "logistic": "Logistic regression", "svm": "Linear SVM",
    "forest": "Random forest", "tree": "Decision tree", "gbm": "Gradient boosting", "xgboost": "XGBoost",
}


def model_spec(name: str, seed: int):
    specs = {
        "dummy": (DummyClassifier(strategy="prior"), {}),
        "logistic": (LogisticRegression(max_iter=2500, class_weight="balanced", random_state=seed), {"model__C": [0.1, 1.0]}),
        "svm": (SVC(kernel="linear", class_weight="balanced", random_state=seed), {"model__C": [0.1, 1.0]}),
        "forest": (RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=seed, n_jobs=1), {"model__min_samples_leaf": [2, 5]}),
        "tree": (DecisionTreeClassifier(class_weight="balanced", random_state=seed), {"model__max_depth": [2, 4]}),
        "gbm": (GradientBoostingClassifier(n_estimators=80, max_depth=2, random_state=seed), {"model__learning_rate": [0.03, 0.1]}),
        "xgboost": (XGBClassifier(n_estimators=80, max_depth=2, learning_rate=0.05, subsample=0.9, colsample_bytree=0.9, random_state=seed, n_jobs=1, tree_method="hist"), {"model__reg_lambda": [1.0, 5.0]}),
    }
    if name not in specs:
        raise DataError(f"Unknown model: {name}")
    estimator, grid = specs[name]
    selector = "passthrough" if name == "dummy" else RFE(
        LogisticRegression(max_iter=2500, class_weight="balanced", random_state=seed),
        n_features_to_select=0.5, step=0.25)
    pipeline = Pipeline([
        ("filter", TrainingFeatureFilter()),
        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scale", StandardScaler()),
        ("select", selector), ("model", estimator),
    ])
    if name != "dummy":
        grid = {"select__n_features_to_select": [0.5, 1.0], **grid}
    return pipeline, grid
