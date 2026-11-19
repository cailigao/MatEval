"""Result Image Analysis: GPT-5.6 Sol five-dimension figure judge (0–100)."""
from __future__ import annotations

SLUG = "result_image_analysis"
TITLE = "Result Image Analysis"
METRIC_NAME = "LLM Score"

DIMENSION_LIMITS = {
    "scientific_correctness": 35,
    "quantitative_fidelity": 25,
    "trend_comparison_fidelity": 20,
    "salient_evidence_coverage": 15,
    "grounding_clarity": 5,
}
VALID_CAPS = {0, 40, 55, 70}


def _score(verdict):
    dimensions = verdict["dimension_scores"]
    if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSION_LIMITS):
        raise ValueError("Judge must return all five rubric dimensions")
    total = 0
    for name, maximum in DIMENSION_LIMITS.items():
        value = dimensions[name]
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
            raise ValueError(f"Invalid {name} score")
        total += value
    cap = verdict.get("cap_applied")
    if cap is not None:
        if isinstance(cap, bool) or not isinstance(cap, int) or cap not in VALID_CAPS:
            raise ValueError("Invalid critical-error cap")
        total = min(total, cap)
    return total


def _evaluate(row):
    verdict = row.get("judge_output")
    if verdict is None:
        raise ValueError("Missing stored image judge output")
    return {"score": _score(verdict), "judge_output": verdict}


def compute(records: list[dict]):
    scored = [{**row, **_evaluate(row)} for row in records]
    mean = sum(row["score"] for row in scored) / len(scored) if scored else float("nan")
    return round(mean, 4), METRIC_NAME, scored
