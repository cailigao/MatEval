"""Microscopy Image Analysis (MIA): per-model MAE_L2 (mean per-record L2 error)."""
from __future__ import annotations

import math

from src.common import extract_json_from_answer

SLUG = "microscopy_image_analysis"
TITLE = "Microscopy Image Analysis"
METRIC_NAME = "MAE"


def _to_float(x) -> float | None:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).strip())
    except Exception:
        return None


def score(r: dict) -> float | None:
    """Return L2 error for one record. The aggregate metric (MAE_L2) is the
    mean of per-record L2 errors, computed across all records of a model."""
    parsed = extract_json_from_answer(r.get("answer", ""))
    if not isinstance(parsed, dict):
        return None
    p_da = _to_float(parsed.get("Da"))
    p_db = _to_float(parsed.get("Db"))
    target = r.get("target") or {}
    if not isinstance(target, dict):
        return None
    g_da = _to_float(target.get("Da"))
    g_db = _to_float(target.get("Db"))
    if p_da is None or p_db is None or g_da is None or g_db is None:
        return None
    e_da = abs(p_da - g_da)
    e_db = abs(p_db - g_db)
    return math.sqrt(e_da * e_da + e_db * e_db)


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    out = [dict(r) for r in records]
    l2s = []
    for r, o in zip(records, out):
        l2 = score(r)
        if l2 is not None:
            l2s.append(l2)
        o["score"] = l2 if l2 is not None else "Error: unparseable"
    metric = sum(l2s) / len(l2s) if l2s else float("nan")
    return metric, METRIC_NAME, out
