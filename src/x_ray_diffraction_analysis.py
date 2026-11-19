"""X-ray Diffraction Analysis: per-record ACC (boolean result match)."""
from __future__ import annotations

from src.common import compute_per_record, extract_json_from_answer

SLUG = "x_ray_diffraction_analysis"
TITLE = "X-ray Diffraction Analysis"
METRIC_NAME = "ACC"
SCALE = 1.0


def score(r: dict) -> float | None:
    answer = r.get("answer", "")
    if not answer:
        return 0.0
    parsed = extract_json_from_answer(answer)
    if not isinstance(parsed, dict):
        return None
    answer_val = parsed.get("result", "")
    if answer_val == "":
        return 0.0
    return 1.0 if r.get("target") == answer_val else 0.0


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
