"""Materials Entity Recognition (mat_NER): per-record F1 (entity set overlap)."""
from __future__ import annotations

import json
import re

from src.common import compute_per_record

SLUG = "materials_entity_recognition"
TITLE = "Materials Entity Recognition"
METRIC_NAME = "F1"
SCALE = 1.0


def _parse_entities(field_data) -> list:
    if isinstance(field_data, list):
        return field_data
    if not isinstance(field_data, str):
        return []
    text = field_data.strip()
    if not text:
        return []
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _to_set(entities: list) -> set:
    s = set()
    for e in entities:
        if not isinstance(e, dict):
            continue
        name = re.sub(r"\s+", "", str(e.get("entity_name", ""))).lower()
        etype = re.sub(r"\s+", "", str(e.get("entity_type", ""))).lower()
        if name and etype:
            s.add((name, etype))
    return s


def _metrics(true_set: set, pred_set: set) -> float:
    tp = len(true_set & pred_set)
    fp = len(pred_set - true_set)
    fn = len(true_set - pred_set)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def score(r: dict) -> float:
    pred_ents = _to_set(_parse_entities(r.get("answer", "")))
    true_ents = _to_set(_parse_entities(r.get("target", "")))
    return _metrics(true_ents, pred_ents)


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
