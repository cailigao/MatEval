"""Objective QA: per-record ACC."""
from __future__ import annotations

import re

from src.common import compute_per_record

SLUG = "objective_qa"
TITLE = "Objective QA"
METRIC_NAME = "ACC"
SCALE = 1.0


def _normalize(answer: str) -> str:
    if len(answer) > 5:
        answer = answer.split("\n")[-1].strip()
    answer = answer.replace(".", "").replace("。", "").lower().strip()
    if any(sep in answer for sep in ("，", ",", "、", "/")):
        answer = re.sub(r"[,，、/\s]", "", answer)
    return answer


def score(r: dict) -> float:
    if not r.get("answer"):
        return 0.0
    return 1.0 if _normalize(r["answer"]) == _normalize(r.get("target", "")) else 0.0


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
