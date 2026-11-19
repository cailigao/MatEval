"""Experimental Parameter Recommendation: GPT-5.6 Sol blind judge (0–100)."""
from __future__ import annotations

WEIGHTS = {
    "precursors": 25,
    "temperatures": 25,
    "substrate": 15,
    "hold_time": 10,
    "carrier_gases_and_flows": 25,
}


def score(verdict):
    dimensions = verdict["dimension_scores"]
    selected = verdict["scorable_dimensions"]
    if not isinstance(selected, list) or not selected or len(selected) != len(set(selected)):
        raise ValueError("Invalid scored dimensions")
    if any(name not in WEIGHTS for name in selected):
        raise ValueError("Unknown scored dimension")
    for name in selected:
        value = dimensions[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 100:
            raise ValueError(f"Invalid {name} score")
    return round(sum(WEIGHTS[name] * dimensions[name] for name in selected) /
                 sum(WEIGHTS[name] for name in selected), 2)


SLUG = "experimental_parameter_recommendation"
TITLE = "Experimental Parameter Recommendation"
METRIC_NAME = "LLM Score"


def _evaluate(row):
    verdict = row.get("judge_output")
    if verdict is None:
        raise ValueError("Missing stored parameter judge output")
    return {"score": score(verdict), "judge_output": verdict}


def compute(records: list[dict]):
    scored = [{**row, **_evaluate(row)} for row in records]
    mean = sum(row["score"] for row in scored) / len(scored) if scored else float("nan")
    return round(mean, 4), METRIC_NAME, scored
