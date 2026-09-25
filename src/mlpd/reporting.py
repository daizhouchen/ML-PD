"""Standalone research figures and a synthetic-only public export gate."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .data import DataError

COLORS = ["#32635B", "#B7793D", "#8C514E", "#7D8A75", "#585B69", "#B1A183", "#8DABA3"]


def _save_figure(fig, path):
    fig.savefig(path, metadata={"Date": None})
    text = path.read_text(encoding="utf-8")
    path.write_bytes(("\n".join(line.rstrip() for line in text.splitlines()) + "\n").encode("utf-8"))


def plot_report(report, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none", "svg.hashsalt": "mlpd-v2", "figure.facecolor": "#FBFAF6", "axes.facecolor": "#FBFAF6"})
    label = "SYNTHETIC PIPELINE DEMONSTRATION" if report["data_kind"] == "synthetic" else "RESEARCH EVALUATION / NOT CLINICAL VALIDATION"
    for task in report["tasks"]:
        models = task["models"]
        fig, ax = plt.subplots(figsize=(9, 4.7))
        for i, model in enumerate(models):
            values = [f["balanced_accuracy"] for f in model["folds"]]
            ax.scatter(values, [i] * len(values), alpha=0.45, color=COLORS[i % len(COLORS)], s=32)
            metric = model["summary"]["balanced_accuracy"]
            ax.errorbar(metric["mean"], i, xerr=metric["std"], color=COLORS[i % len(COLORS)], fmt="D", capsize=4)
        ax.set(yticks=range(len(models)), yticklabels=[m["name"] for m in models], xlim=(0, 1), xlabel="Outer-fold balanced accuracy · mean ± fold SD")
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=0.15)
        fig.suptitle(f"{task['id']} / subject-separated nested CV", x=0.03, ha="left", fontweight="bold")
        fig.text(0.03, 0.02, label + " · SD is not a confidence interval", fontsize=8, color="#6D726B")
        fig.tight_layout(rect=(0, 0.06, 1, 0.92))
        _save_figure(fig, output / f"{task['id']}-comparison.svg")
        plt.close(fig)
        chosen = next((m for m in models if m["id"] == "logistic"), models[0])
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
        for i, curve in enumerate(chosen["roc"]):
            axes[0].plot(curve["fpr"], curve["mean_tpr"], color=COLORS[i], label=curve["class"])
        axes[0].plot([0, 1], [0, 1], linestyle="--", color="#A9AAA2")
        axes[0].set(xlabel="False positive rate", ylabel="Mean true positive rate", title="Mean outer-fold OVR ROC")
        axes[0].legend(frameon=False)
        matrix = np.array(chosen["confusion_matrix"])
        axes[1].imshow(matrix, cmap="YlGn", vmin=0)
        axes[1].set(xticks=range(len(task["classes"])), yticks=range(len(task["classes"])),
                    xticklabels=task["classes"], yticklabels=task["classes"], xlabel="Predicted label", ylabel="Observed label", title="Out-of-fold confusion matrix")
        for (row, col), value in np.ndenumerate(matrix):
            axes[1].text(col, row, str(value), ha="center", va="center", color="white" if value > matrix.max() * 0.65 else "#213F38")
        fig.suptitle(f"{task['id']} / {chosen['name']} (prespecified reference)", x=0.03, ha="left", fontweight="bold")
        fig.text(0.03, 0.02, label, fontsize=8, color="#6D726B")
        fig.tight_layout(rect=(0, 0.06, 1, 0.91))
        _save_figure(fig, output / f"{task['id']}-reference.svg")
        plt.close(fig)


def publish_demo(report_path, output):
    """Only numerical synthetic fixtures can enter the public documentation directory."""
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if report.get("data_kind") != "synthetic":
        raise DataError("Public export only accepts synthetic runs. Private/public research data require a separate disclosure review.")
    for task in report["tasks"]:
        for model in task["models"]:
            if any(not f["feature"].startswith("synthetic_feature_") for f in model["feature_stability"]):
                raise DataError("Non-synthetic feature names detected; refusing automatic public export.")
    # Do not publish subject membership hashes, identifiers, or local filesystem paths.
    for task in report["tasks"]:
        for model in task["models"]:
            for fold in model["folds"]:
                fold.pop("train_membership_sha256", None)
                fold.pop("test_membership_sha256", None)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "demo-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    plot_report(report, output / "figures")
    return report
