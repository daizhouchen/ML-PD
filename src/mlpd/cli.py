import argparse
import json
import sys
from pathlib import Path

from .data import DataError, TASKS, load_dataset, make_demo
from .evaluate import run_experiment
from .models import MODEL_NAMES
from .reporting import plot_report, publish_demo


def main(argv=None):
    parser = argparse.ArgumentParser(prog="mlpd", description="Metabolomics research workflow; not a clinical diagnostic tool.")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Generate a clearly labelled synthetic input fixture")
    demo.add_argument("--output", required=True)
    demo.add_argument("--seed", type=int, default=2026)
    demo.add_argument("--samples", type=int, default=180)
    validate = commands.add_parser("validate", help="Validate input schema and data without training")
    run = commands.add_parser("run", help="Run subject-separated nested cross-validation")
    for command in (validate, run):
        command.add_argument("--data", required=True)
        command.add_argument("--schema", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--tasks", nargs="+", choices=list(TASKS), default=list(TASKS))
    run.add_argument("--models", nargs="+", choices=list(MODEL_NAMES), default=list(MODEL_NAMES))
    run.add_argument("--outer-folds", type=int, default=5)
    run.add_argument("--inner-folds", type=int, default=3)
    run.add_argument("--seed", type=int, default=2026)
    run.add_argument("--jobs", type=int, default=1)
    publish = commands.add_parser("publish-demo", help="Export synthetic aggregate results and figures for the showcase")
    publish.add_argument("--report", required=True)
    publish.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            data_path, schema_path = make_demo(args.output, args.seed, args.samples)
            print(f"Synthetic fixture: {data_path}\nSchema: {schema_path}\nNo clinical or metabolite interpretation.")
        elif args.command == "validate":
            data = load_dataset(args.data, json.loads(Path(args.schema).read_text(encoding="utf-8-sig")))
            print(json.dumps({"status": "valid", "samples": len(data.y), "subjects": len(set(data.groups)),
                              "features": data.X.shape[1], "classes": data.classes, "data_kind": data.data_kind,
                              "notes": data.notes}, ensure_ascii=False, indent=2))
        elif args.command == "run":
            report = run_experiment(args.data, args.schema, args.output, tasks=args.tasks, models=args.models,
                                    outer_folds=args.outer_folds, inner_folds=args.inner_folds,
                                    seed=args.seed, jobs=args.jobs)
            plot_report(report, Path(args.output) / "figures")
            print(f"Completed: {args.output}/report.json")
        else:
            publish_demo(args.report, args.output)
            print(f"Synthetic aggregate showcase exported: {args.output}")
    except (DataError, FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"ML-PD: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
