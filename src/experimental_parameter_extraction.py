"""Experimental Parameter Extraction (IE_exp_params): per-model F1 (per-file aggregation)."""
from __future__ import annotations

import json
import re
from collections import defaultdict

try:
    from json_repair import repair_json
except ImportError:
    repair_json = None

SLUG = "experimental_parameter_extraction"
TITLE = "Experimental Parameter Extraction"
METRIC_NAME = "F1"


def _extract_json(answer_str: str) -> dict:
    if "```json" in answer_str:
        match = re.search(r"```json(.*?)```", answer_str, re.DOTALL)
        answer_str = match.group(1).strip() if match else answer_str
    try:
        return json.loads(repair_json(answer_str)) if repair_json else json.loads(answer_str)
    except Exception:
        return {}


def _score_records(records: list[dict], cvd_scale: int = 1, piezo_scale: int = 1) -> float:
    """Aggregate per-filename P/R/F1, return mean F1 across filenames.

    `cvd_scale`/`piezo_scale` multiply the len(target_records) and len(predict)
    for CVD/piezo task_types (the testset expands each CVD item into 19 sub-
    fields and each piezo item into 16 sub-fields).
    """
    file_agg = defaultdict(lambda: {"score": 0.0, "target": 0, "predict": 0})
    for r in records:
        fname = r.get("filename", "")
        if not fname:
            continue
        task_type = r.get("task_type", "")
        len_t = r.get("len(target_records)", 0) or r.get("len_target_records", 0) or 0
        len_p = r.get("len_predict", 0) or r.get("len_predict", 0) or 0
        if task_type == "exp_params_CVD":
            len_t *= 19 * cvd_scale
            len_p *= 19 * cvd_scale
        elif task_type == "exp_params_piezo":
            len_t *= 16 * piezo_scale
            len_p *= 16 * piezo_scale
        ans = _extract_json(r.get("answer", ""))
        score_val = 0.0
        if isinstance(ans, dict):
            for v in ans.values():
                try:
                    score_val += max(0.0, min(1.0, float(v)))
                except (ValueError, TypeError):
                    continue
        file_agg[fname]["score"] += score_val
        file_agg[fname]["target"] += len_t
        file_agg[fname]["predict"] += len_p
    f1s = []
    for fname, c in file_agg.items():
        s, t, p = c["score"], c["target"], c["predict"]
        precision = s / p if p > 0 else 0.0
        recall = s / t if t > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        f1s.append(f1)
    return sum(f1s) / len(f1s) if f1s else 0.0


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric = _score_records(records)
    out = [dict(r) for r in records]
    for r in out:
        r["score"] = metric
    return metric, METRIC_NAME, out
