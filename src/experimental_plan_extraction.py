"""Experimental Plan Extraction (IE_exp_scheme): per-model F1 (per-record F1 from tp/fp/fn)."""
from __future__ import annotations

import json
import re

try:
    from json_repair import repair_json
except ImportError:
    repair_json = None

SLUG = "experimental_plan_extraction"
TITLE = "Experimental Plan Extraction"
METRIC_NAME = "F1"


def _extract_json(answer_str: str) -> dict:
    if "```json" in answer_str:
        match = re.search(r"```json(.*?)```", answer_str, re.DOTALL)
        answer_str = match.group(1).strip() if match else answer_str
    try:
        return json.loads(repair_json(answer_str)) if repair_json else json.loads(answer_str)
    except Exception:
        return {}


def _score_records(records: list[dict]) -> float:
    """IE_exp_scheme: judge `answer` is a JSON with `summary.{tp,fp,fn}_count`.

    The metric is per-file F1 (computed from tp/fp/fn), averaged across files.
    """
    f1s = []
    for r in records:
        ans = _extract_json(r.get("answer", ""))
        if not isinstance(ans, dict):
            continue
        summary = ans.get("summary", {})
        if not isinstance(summary, dict):
            continue
        tp = summary.get("tp_count", 0) or 0
        fp = summary.get("fp_count", 0) or 0
        fn = summary.get("fn_count", 0) or 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * precision * recall / (precision + recall)
        f1s.append(f1)
    return sum(f1s) / len(f1s) if f1s else 0.0


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric = _score_records(records)
    out = [dict(r) for r in records]
    for r in out:
        r["score"] = metric
    return metric, METRIC_NAME, out
