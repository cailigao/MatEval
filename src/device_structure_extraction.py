"""Device Structure Extraction (IE_dev_struc): per-record Avg of nested judge scores."""
from __future__ import annotations

import json

from src.common import compute_per_record

try:
    from json_repair import repair_json
except ImportError:
    repair_json = None

SLUG = "device_structure_extraction"
TITLE = "Device Structure Extraction"
METRIC_NAME = "Avg"
SCALE = 1.0


def _extract_score_average(answer_str: str) -> float | None:
    if not answer_str:
        return None
    try:
        answer_json = json.loads(repair_json(answer_str)) if repair_json else json.loads(answer_str)
    except Exception:
        return None
    try:
        device = answer_json["devices"][0]
        layer_fields_score = device["layerFieldsScore"]
    except Exception:
        return None
    scores = []
    for layer_name, layer_fields in layer_fields_score.items():
        for field_name, field_info in layer_fields.items():
            score = field_info.get("score")
            if score is not None and isinstance(score, (int, float)):
                scores.append(score)
    if not scores:
        return None
    return round(sum(scores) / len(scores), 3)


def score(r: dict) -> float | None:
    avg = _extract_score_average(r.get("answer", ""))
    return float(avg) if avg is not None else None


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
