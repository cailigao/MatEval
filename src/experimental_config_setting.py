"""Experimental Config Setting (YAML generation): per-record ACC (0-100)."""
from __future__ import annotations

import re

from src.common import compute_per_record

SLUG = "experimental_config_setting"
TITLE = "Experimental Config Setting"
METRIC_NAME = "ACC"
SCALE = 100.0


def _clean_output(text: str) -> str:
    try:
        import yaml  # noqa: F401
    except ImportError:
        return text
    match = re.search(r"```yaml\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    text = text.replace("```", "").strip()
    lines = text.split("\n")
    if lines and lines[0].strip().lower() in ("yaml", "%yaml"):
        text = "\n".join(lines[1:]).strip()
    if text.startswith("---"):
        text = text[3:].strip()
    return text


def evaluate(pred_text: str, gt_text: str) -> int:
    try:
        import yaml
    except ImportError:
        return 0
    score = 0
    try:
        gt_obj = yaml.safe_load(gt_text)
    except Exception:
        return 0
    try:
        pred_obj = yaml.safe_load(_clean_output(pred_text))
        if not isinstance(pred_obj, dict):
            raise ValueError("not a dict")
        score += 20
    except Exception:
        return 0
    if "process_step" in pred_obj and "parameters" in pred_obj:
        params = pred_obj["parameters"]
        if isinstance(params, dict) and all(k in params for k in ["temperature", "pressure", "duration"]):
            score += 30
        else:
            return score
    else:
        return score
    ok = True
    gt_params = gt_obj.get("parameters", {})
    pred_params = pred_obj.get("parameters", {})
    if str(pred_obj.get("process_step")).lower() != str(gt_obj.get("process_step")).lower():
        ok = False
    for key in ["temperature", "pressure", "duration"]:
        try:
            if int(float(pred_params.get(key, -1))) != int(float(gt_params.get(key, -2))):
                ok = False
        except Exception:
            ok = False
    if "gas_flow" in gt_params:
        gt_gas = gt_params["gas_flow"]
        pred_gas = pred_params.get("gas_flow", {})
        if not pred_gas:
            ok = False
        else:
            for gk, gv in gt_gas.items():
                try:
                    if int(float(pred_gas.get(gk, -999))) != int(float(gv)):
                        ok = False
                except Exception:
                    ok = False
    if ok:
        score += 50
    return score


def score(r: dict) -> float:
    answer = r.get("answer", "")
    gt_text = r.get("target", "")
    if not answer:
        return 0.0
    return float(evaluate(answer, gt_text))


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
