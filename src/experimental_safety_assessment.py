"""Experimental Safety Assessment: per-record ACC (Yes/No)."""
from __future__ import annotations

from src.common import compute_per_record, extract_json_from_answer

SLUG = "experimental_safety_assessment"
TITLE = "Experimental Safety Assessment"
METRIC_NAME = "ACC"
SCALE = 1.0


def score(r: dict) -> float | None:
    if not r.get("answer"):
        return 0.0
    parsed = extract_json_from_answer(r["answer"])
    if not isinstance(parsed, dict):
        return None
    answer = parsed.get("answer", "")
    if isinstance(answer, str):
        answer = answer.strip()
    return 1.0 if r.get("target") == answer else 0.0


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
