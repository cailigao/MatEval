"""Synthesis Action Retrieval (SAR): per-record F1 (token/tag tuple set overlap)."""
from __future__ import annotations

import json

try:
    from json_repair import repair_json
except ImportError:
    repair_json = None

from src.common import compute_per_record

SLUG = "synthesis_action_retrieval"
TITLE = "Synthesis Action Retrieval"
METRIC_NAME = "F1"
SCALE = 1.0


def _dict_to_unit_set(d: list) -> set:
    units = set()
    for token in d:
        if isinstance(token, dict):
            units.add((token.get("token"), token.get("tag")))
    return units


def _get_score(ref_dict, pred_dict) -> float:
    try:
        ref = json.loads(repair_json(ref_dict)) if isinstance(ref_dict, str) and repair_json else ref_dict
        pred = json.loads(repair_json(pred_dict)) if isinstance(pred_dict, str) and repair_json else pred_dict
        if not isinstance(ref, list):
            return 0.0
        if not isinstance(pred, list):
            return 0.0
        ref_units = _dict_to_unit_set(ref)
        pred_units = _dict_to_unit_set(pred)
        if not ref_units and not pred_units:
            return 1.0
        if not ref_units or not pred_units:
            return 0.0
        tp = len(ref_units & pred_units)
        fp = len(pred_units - ref_units)
        fn = len(ref_units - pred_units)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        if precision + recall == 0:
            return 0.0
        return round(2 * precision * recall / (precision + recall), 4)
    except Exception:
        return 0.0


def score(r: dict) -> float:
    return _get_score(r.get("target"), r.get("answer", ""))


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
