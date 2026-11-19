"""Abnormal-input Detection: per-record ACC (class_id/class_name match)."""
from __future__ import annotations

from src.common import compute_per_record, extract_json_from_answer

SLUG = "abnormal_input_detection"
TITLE = "Abnormal-input Detection"
METRIC_NAME = "ACC"
SCALE = 1.0

CLASS_DICT_ABNORMAL = {"1": "Irrelevant", "2": "Ambiguous", "3": "Valid"}


def score(r: dict) -> float | None:
    if not r.get("answer"):
        return 0.0
    parsed = extract_json_from_answer(r["answer"])
    if not isinstance(parsed, dict):
        return None
    class_id = str(parsed.get("class_id", ""))
    class_name = parsed.get("class_name", "")
    if class_id not in CLASS_DICT_ABNORMAL or class_name != CLASS_DICT_ABNORMAL[class_id]:
        return 0.0
    return 1.0 if class_name == r.get("target") else 0.0


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
