"""MP Database Call: per-record ACC (AST-based Python code equivalence)."""
from __future__ import annotations

import ast
import re

from src.common import compute_per_record

SLUG = "mp_database_call"
TITLE = "MP Database Call"
METRIC_NAME = "ACC"
SCALE = 1.0


def _clean_code(code: str) -> str:
    lines = code.split("\n")
    cleaned = []
    for line in lines:
        line = re.sub(r"#.*$", "", line).strip()
        if line:
            cleaned.append(line)
    return re.sub(r"\s+", " ", " ".join(cleaned))


def _parse_expr(node) -> object:
    try:
        if isinstance(node, ast.Attribute):
            parent = _parse_expr(node.value)
            return f"{parent}.{node.attr}"
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.List):
            items = []
            for item in node.elts:
                v = _parse_expr(item)
                if v is not None:
                    items.append(v)
            return items
        if isinstance(node, (ast.Tuple, ast.Constant)):
            return ast.literal_eval(node)
        return None
    except Exception:
        return None


def _normalize_param(value) -> object:
    if isinstance(value, list):
        return sorted(value)
    return value


def _extract_imports(cleaned_code: str) -> list:
    return [re.sub(r"\s+", " ", imp) for imp in
            re.findall(r"(from \S+ import \S+|import \S+)", cleaned_code)]


def _extract_mpr_path(cleaned_code: str):
    m = re.search(r"mpr\.([\w\.]+)\.search", cleaned_code)
    return m.group(1) if m else None


def _parse_search_params(cleaned_code: str):
    try:
        m = re.search(r"search\(\s*((?:[^()]+|\((?:[^()]+|\([^()]*\))*\))*)\s*\)",
                      cleaned_code)
        if not m:
            return None
        args_str = m.group(1).strip()
        if not args_str:
            return ([], tuple())
        tree = ast.parse(f"def temp({args_str}): pass")
        func_def = tree.body[0]
        arg_names = [a.arg for a in func_def.args.args]
        defaults = func_def.args.defaults
        n_def = len(defaults)
        n_args = len(arg_names)
        kwargs = {}
        for i in range(n_def):
            arg_idx = n_args - n_def + i
            v = _parse_expr(defaults[i])
            if v is None:
                return None
            kwargs[arg_names[arg_idx]] = _normalize_param(v)
        return ([], tuple(sorted(kwargs.items())))
    except Exception:
        return None


def _are_equivalent(code1: str, code2: str) -> bool:
    """Port of src/MP_call/mp_eval.are_code_snippets_equivalent.
    Compares imports, mpr call path, and normalized search kwargs."""
    c1 = _clean_code(code1)
    c2 = _clean_code(code2)
    if sorted(_extract_imports(c1)) != sorted(_extract_imports(c2)):
        return False
    if _extract_mpr_path(c1) != _extract_mpr_path(c2):
        return False
    p1 = _parse_search_params(c1)
    p2 = _parse_search_params(c2)
    if p1 is None or p2 is None or p1 != p2:
        return False
    return True


def score(r: dict) -> float:
    answer = r.get("answer", "") or ""
    target = r.get("target", "")
    if not answer:
        return 0.0
    code = answer
    m = re.search(r"```python\n(.*?)```", answer, re.DOTALL)
    if m:
        code = m.group(1).strip()
    if isinstance(target, dict):
        target_codes = list(target.values())
    elif isinstance(target, list):
        target_codes = target
    else:
        target_codes = [str(target)]
    if not code:
        return 0.0
    for tc in target_codes:
        try:
            if _are_equivalent(code, str(tc)):
                return 1.0
        except Exception:
            continue
    return 0.0


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
