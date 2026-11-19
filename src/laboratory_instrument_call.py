"""Laboratory Instrument Call: per-record ACC (AST-based function-call equivalence)."""
from __future__ import annotations

import ast
import re

from src.common import compute_per_record

SLUG = "laboratory_instrument_call"
TITLE = "Laboratory Instrument Call"
METRIC_NAME = "ACC"
SCALE = 1.0


def _parse_function_call(code_str: str) -> dict | None:
    try:
        code_str = code_str.strip()
        block = re.search(r"```(?:python)?\s*(.*?)\s*```", code_str, re.DOTALL)
        if block:
            code_str = block.group(1).strip()
        code_str = code_str.replace("`", "").strip()
        lines = [l for l in code_str.split("\n") if l.strip() and not l.strip().startswith("#")]
        if not lines:
            return None
        code_str = lines[0].strip()
        tree = ast.parse(code_str)
        if not isinstance(tree, ast.Module) or len(tree.body) != 1:
            return None
        expr = tree.body[0]
        if not isinstance(expr, ast.Expr) or not isinstance(expr.value, ast.Call):
            return None
        call = expr.value
        func_name = call.func.id
        kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in call.keywords}
        positional = [ast.literal_eval(a) for a in call.args]
        return {"name": func_name, "args": kwargs, "positional": positional}
    except Exception:
        return {"error": str(code_str[:80])}


def evaluate(pred_str: str, gt_str: str) -> int:
    pred = _parse_function_call(pred_str)
    gt = _parse_function_call(gt_str)
    if not pred or "error" in pred:
        return 0
    if "error" in gt:
        return 0
    if pred["name"] != gt["name"]:
        return 0
    pa, ga = pred["args"], gt["args"]
    pp, gp = pred.get("positional", []), gt.get("positional", [])
    if len(pa) + len(pp) != len(ga) + len(gp):
        return 0
    if ga and pa:
        for k, v in ga.items():
            if k not in pa:
                return 0
            if pa[k] != v:
                return 0
        return 1
    if ga and pp:
        for i, (pv, gv) in enumerate(zip(pp, list(ga.values()))):
            if pv != gv:
                return 0
        return 1
    if gp and pp:
        for i, (pv, gv) in enumerate(zip(pp, gp)):
            if pv != gv:
                return 0
        return 1
    return 1


def score(r: dict) -> float:
    answer = r.get("answer", "")
    gt_str = r.get("target", "")
    if not answer:
        return 0.0
    return float(evaluate(answer, gt_str))


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
