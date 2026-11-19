"""Experimental Plan Recommendation: GPT-5.6 Sol atomic-error judge (0–100)."""
from __future__ import annotations

import json
from pathlib import Path

WEIGHTS = {
    "evidence_fidelity": 0.35,
    "plan_quality": 0.40,
    "decision_and_verification": 0.25,
}
POINTS = {name: round(weight * 100) for name, weight in WEIGHTS.items()}
PENALTIES = {"minor": 2, "moderate": 7, "major": 15, "fatal": 40}


def compute_score(verdict):
    roots = {}
    for item in verdict["errors"]:
        dimension = item["dimension"]
        severity = item["severity"]
        if dimension not in POINTS or severity not in PENALTIES:
            raise ValueError("Invalid plan judge error")
        identifier = str(item["root_cause_id"])
        if identifier not in roots or PENALTIES[severity] > PENALTIES[roots[identifier]["severity"]]:
            roots[identifier] = item
    balance = dict(POINTS)
    for item in roots.values():
        dimension = item["dimension"]
        balance[dimension] = max(0, balance[dimension] - PENALTIES[item["severity"]])
    return sum(balance.values())



SLUG = "experimental_plan_recommendation"
TITLE = "Experimental Plan Recommendation"
METRIC_NAME = "LLM Score"

# Optional sidecar benchmark file. Each data record already carries its own
# `target`, so this is only used when present (e.g. a vendored reference set);
# otherwise the per-idx targets are rebuilt from the records themselves.
BENCHMARK = Path(__file__).with_name("experimental_plan_recommendation_benchmark.jsonl")


def _benchmark_from_file():
    with BENCHMARK.open(encoding="utf-8") as stream:
        return {json.loads(line)["idx"]: json.loads(line) for line in stream if line.strip()}


def _benchmark_from_records(records):
    # `target` is identical across models for a given idx (verified on the
    # shipped data), so the first sighting per idx is the canonical target.
    tasks = {}
    for row in records:
        idx = row.get("idx")
        if isinstance(idx, int) and idx not in tasks:
            tasks[idx] = row
    return tasks


def _evaluate(row, tasks):
    idx = row["idx"]
    if not isinstance(idx, int) or idx not in tasks:
        raise ValueError(f"Unknown experimental-plan idx: {idx}")
    task = tasks[idx]
    if row["target"] != task["target"]:
        raise ValueError(f"Target mismatch for experimental-plan idx {idx}")
    verdict = row.get("judge_output")
    if verdict is not None and {"id", "score", *WEIGHTS} == verdict.keys():
        # The supplemental run archived the three dimension grades directly.
        for dimension in WEIGHTS:
            value = verdict[dimension]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 100:
                raise ValueError(f"Invalid supplemental grade for {dimension}")
        score = round(sum(weight * verdict[key] for key, weight in WEIGHTS.items()), 2)
        return {"score": score, "judge_output": verdict}
    if verdict is None:
        raise ValueError("Missing stored plan judge output")
    score = compute_score(verdict)
    return {"score": score, "judge_output": verdict}


def compute(records: list[dict]):
    if BENCHMARK.is_file():
        tasks = _benchmark_from_file()
    else:
        tasks = _benchmark_from_records(records)
    scored = [{**row, **_evaluate(row, tasks)} for row in records]
    mean = sum(row["score"] for row in scored) / len(scored) if scored else float("nan")
    return round(mean, 4), METRIC_NAME, scored
