"""Standalone metric calculator for the 24 MatEval tasks.

Reads the 24 task data files from data/<slug>.jsonl, computes per-task per-model
metrics via the per-task module in tasks/<slug>.py, and writes:
  - results/<slug>__<model>__scores.jsonl  (per-record scores, minimal fields)
  - results/summary.json         (per-task per-model aggregate metric)
  - results/summary.xlsx          (pivot table: models x tasks)

Each per-task module exports SLUG, TITLE, METRIC_NAME, and compute(records)
-> (metric, metric_name, scored_records).

Usage:
  python calculator.py
  python calculator.py --data-dir data --output-dir results
"""
from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path

import src as tasks
from src.common import read_jsonl, write_json, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # task -> model -> {metric, metric_name, n, valid_count, empty_as_0}
    summary: dict[str, dict[str, dict]] = defaultdict(dict)
    # model -> {task: metric}
    pivot: dict[str, dict[str, float]] = defaultdict(dict)

    for slug in tasks.SLUGS:
        title = tasks.get_title(slug)
        data_path = args.data_dir / f"{slug}.jsonl"
        if not data_path.is_file():
            print(f"[skip] {slug}: missing {data_path}")
            continue
        records = list(read_jsonl(data_path))
        if not records:
            print(f"[skip] {slug}: no records")
            continue

        # Group by model
        by_model = defaultdict(list)
        for r in records:
            m = r.get("model")
            if m:
                by_model[m].append(r)

        print(f"\n=== {title} ({slug}) ===")
        compute_fn = tasks.get_compute(slug)
        for model in sorted(by_model):
            model_records = by_model[model]
            try:
                metric, metric_name, scored = compute_fn(model_records)
            except Exception as exc:  # pragma: no cover - keep one bad task from aborting the run
                print(f"  [error] {model}: {exc}")
                continue
            n = len(model_records)
            # valid_count: per-record scorers report None on parse failure;
            # the count of non-None numeric scores.
            valid_count = sum(
                1 for o in scored
                if isinstance(o.get("score"), (int, float)) and not (
                    isinstance(o.get("score"), float) and math.isnan(o["score"])
                )
            )
            if valid_count == 0 and metric == metric:  # not NaN
                valid_count = n
            summary[slug][model] = {
                "metric": round(metric, 4) if not (isinstance(metric, float) and math.isnan(metric)) else None,
                "metric_name": metric_name,
                "n": n,
                "valid_count": valid_count,
            }
            pivot[model][slug] = round(metric, 4) if not (isinstance(metric, float) and math.isnan(metric)) else None
            score_path = args.output_dir / f"{slug}__{model}__scores.jsonl"
            write_jsonl(score_path, scored)
            print(f"  {model}: {metric_name}={metric:.4f} (valid={valid_count}/{n})")

    # Write summary.json
    summary_out = {slug: dict(summary[slug]) for slug in summary}
    write_json(args.output_dir / "summary.json", summary_out)
    print(f"\nWrote {args.output_dir / 'summary.json'}")

    # Write summary.xlsx (models x tasks pivot)
    try:
        import pandas as pd
        models = sorted(pivot)
        rows = []
        for model in models:
            row = {"model": model}
            for slug in tasks.SLUGS:
                row[slug] = pivot[model].get(slug)
            rows.append(row)
        df = pd.DataFrame(rows)
        xlsx_path = args.output_dir / "summary.xlsx"
        df.to_excel(xlsx_path, index=False, sheet_name="metrics")
        print(f"Wrote {xlsx_path}")
    except ImportError:
        print("pandas not available; skipping summary.xlsx")


if __name__ == "__main__":
    main()
