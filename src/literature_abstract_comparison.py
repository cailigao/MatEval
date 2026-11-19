"""Literature Abstract Comparison: per-record Score (0-100, LLM-judge)."""
from __future__ import annotations

from src.common import compute_per_record, extract_json_from_answer

SLUG = "literature_abstract_comparison"
TITLE = "Literature Abstract Comparison"
METRIC_NAME = "Score"
SCALE = 100.0


def score(r: dict) -> float | None:
    parsed = extract_json_from_answer(r.get("answer", ""))
    if not isinstance(parsed, dict):
        return None
    try:
        return float(parsed.get("final_score"))
    except (TypeError, ValueError):
        return None


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
