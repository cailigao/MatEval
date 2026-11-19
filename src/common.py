"""Shared helpers for the per-task metric calculators."""
from __future__ import annotations

import json
import re
from pathlib import Path

try:
    import json_repair
except ImportError:
    json_repair = None


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def read_jsonl(path: Path):
    if not path.is_file():
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def extract_json_from_answer(answer):
    """Parse a JSON object from a model answer.

    Handles ```json``` fenced blocks; falls back to repairing the raw text.
    """
    if not isinstance(answer, str):
        return {}
    if json_repair is None:
        match = re.search(r"```json\s*(.*?)\s*```", answer, re.DOTALL)
        text = match.group(1).strip() if match else answer
        try:
            return json.loads(text)
        except Exception:
            return {}
    match = re.search(r"```json\s*(.*?)\s*```", answer, re.DOTALL)
    if match:
        try:
            return json_repair.loads(match.group(1).strip())
        except Exception:
            return {}
    try:
        return json_repair.loads(answer)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Generic per-record scoring loop
# ---------------------------------------------------------------------------

def score_records(records: list[dict], metric_fn, *, scale: float = 1.0) -> tuple[float, float, int, int, list[dict]]:
    """Score each record. Returns (empty_excluded, empty_as_0, valid_count, n, out_records).

    `metric_fn(record)` returns a numeric score, `None` (record is invalid /
    unparseable; excluded from the mean), or a string error (also excluded).

    - `empty_excluded = valid_sum / valid_count` (excludes invalid records)
    - `empty_as_0 = valid_sum / n` (treats invalid as 0)
    - If `valid_count == 0`, `empty_excluded` is `float('nan')`.

    The accumulation `valid_sum += value / scale` matches the upstream xlsx
    target (run_multi_judge_eval.py) — preserves IEEE-754 ulp drift exactly.
    """
    valid_sum = 0.0
    valid_count = 0
    n = len(records)
    out = []
    for r in records:
        out_rec = dict(r)
        try:
            value = metric_fn(r)
            if value is None:
                out_rec["score"] = None
                out.append(out_rec)
                continue
            if isinstance(value, str):
                raise ValueError(value)
            value = float(value)
            out_rec["score"] = value
            valid_sum += value / scale
            valid_count += 1
        except Exception as e:
            out_rec["score"] = f"Error: {e}"
        out.append(out_rec)
    empty_excluded = (valid_sum / valid_count) if valid_count else float("nan")
    empty_as_0 = (valid_sum / n) if n else 0.0
    return empty_excluded, empty_as_0, valid_count, n, out


def compute_per_record(records: list[dict], metric_fn, *, scale: float = 1.0,
                       exclude_idx: set | None = None) -> tuple[float, str, list[dict]]:
    """Standard per-record scoring driver.

    Returns (empty_excluded, metric_name, scored_records).
    """
    if exclude_idx:
        records = [r for r in records if r.get("idx") not in exclude_idx]
    empty_excluded, _, _, _, out = score_records(records, metric_fn, scale=scale)
    return empty_excluded, out
