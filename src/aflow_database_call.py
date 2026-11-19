"""AFLOW Database Call: per-record ACC (URL parameter equivalence)."""
from __future__ import annotations

from src.common import compute_per_record

SLUG = "aflow_database_call"
TITLE = "AFLOW Database Call"
METRIC_NAME = "ACC"
SCALE = 1.0


def _are_equivalent(code1: str, code2: str) -> bool:
    code1 = code1.replace("(*)", "").replace(" ", "")
    code2 = code2.replace("(*)", "").replace(" ", "")

    def extract_params(url: str) -> list[str]:
        parts = url.split("?", 1)
        query_part = parts[1] if len(parts) > 1 else ""
        params = []
        current = ""
        depth = 0
        for ch in query_part:
            if ch == "(":
                depth += 1
                current += ch
            elif ch == ")":
                depth = max(0, depth - 1)
                current += ch
            elif ch == "," and depth == 0:
                cleaned = current.strip()
                if cleaned:
                    params.append(cleaned)
                current = ""
            else:
                current += ch
        cleaned = current.strip()
        if cleaned:
            params.append(cleaned)
        return params

    return sorted(extract_params(code1)) == sorted(extract_params(code2))


def score(r: dict) -> float:
    code = r.get("answer", "") or ""
    target = r.get("target", "") or ""
    try:
        return 1.0 if _are_equivalent(code, target) else 0.0
    except Exception:
        return 0.0


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
