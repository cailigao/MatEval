"""Literature-Based QA (RAG QA): per-record Score (0-1, LLM-judge with score/5)."""
from __future__ import annotations

from src.common import compute_per_record, extract_json_from_answer

SLUG = "literature_based_qa"
TITLE = "Literature-Based QA"
METRIC_NAME = "Score"
SCALE = 1.0


def score(r: dict) -> float | None:
    parsed = extract_json_from_answer(r.get("answer", ""))
    if not isinstance(parsed, dict):
        return None
    s = parsed.get("score")
    try:
        return float(s) / 5.0
    except (TypeError, ValueError):
        return None


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
