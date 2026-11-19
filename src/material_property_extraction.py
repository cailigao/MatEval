"""Material Property Extraction (IE_mat_prop): per-model F1 (per-text_index aggregation).

The judge `answer` is a JSON of {field: {score: 0..1}}. The metric is
Precision/Recall/F1 per (doi, source_file, text_index), then averaged.
len(predict) and len(target) are on the record (not the judge file); we
scale the score by 4 per the original scorer (each field scored 0..1, 4
fields per property).

The testset has 150 ids spanning 2..166 with 16 gaps (1, 57, 65, 70, 74-76,
78, 80, 91, 95, 98, 101, 117-118, 147). A model can be missing some
text_indexes (truncated/empty answers), so the xlsx-matching metric treats
each missing id as 0 and divides by 150, not by the count of present ids.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict

try:
    from json_repair import repair_json
except ImportError:
    repair_json = None

SLUG = "material_property_extraction"
TITLE = "Material Property Extraction"
METRIC_NAME = "F1"

TESTSET_IDS = [
    2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
    22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
    40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 58,
    59, 60, 61, 62, 63, 64, 66, 67, 68, 69, 71, 72, 73, 77, 79, 81, 82, 83,
    84, 85, 86, 87, 88, 89, 90, 92, 93, 94, 96, 97, 99, 100, 102, 103, 104,
    105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 119, 120,
    121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134,
    135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 148, 149,
    150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163,
    164, 165, 166,
]


def _extract_json(answer_str: str) -> dict:
    if "```json" in answer_str:
        match = re.search(r"```json(.*?)```", answer_str, re.DOTALL)
        answer_str = match.group(1).strip() if match else answer_str
    try:
        return json.loads(repair_json(answer_str)) if repair_json else json.loads(answer_str)
    except Exception:
        return {}


def _score_records(records: list[dict]) -> float:
    # Group records by (doi, source_file, text_index). Original code stores
    # the F1 into score_dict[text_index] (NOT the composite key), so when
    # multiple (doi, source_file) share a text_index, the last one wins. We
    # replicate that behavior to match the original metric exactly.
    information_doi = {}
    doi_score_dict = defaultdict(float)
    for r in records:
        if r.get("task_type") and r["task_type"] != "Material Property Extraction":
            continue
        key = f"{r.get('doi')},{r.get('source_file')},{r.get('text_index')}"
        information_doi[key] = {
            "len_predict": r.get("len_predict", 0) or 0,
            "len_target": r.get("len_target", 0) or 0,
            "text_index": r.get("text_index"),
        }
        ans = _extract_json(r.get("answer", ""))
        single_score = 0.0
        if isinstance(ans, dict):
            for val in ans.values():
                if isinstance(val, dict) and "score" in val:
                    try:
                        single_score += float(val["score"])
                    except (TypeError, ValueError):
                        continue
        doi_score_dict[key] += single_score
    score_dict = {}
    for item_key, item_info in information_doi.items():
        lp = item_info["len_predict"]
        lt = item_info["len_target"]
        text_index = item_info["text_index"]
        total = doi_score_dict.get(item_key, 0.0)
        precision = total / (4 * lp) if lp > 0 else 0.0
        recall = total / (4 * lt) if lt > 0 else 0.0
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * precision * recall / (precision + recall)
        score_dict[text_index] = round(f1, 4)
    if not score_dict:
        return 0.0
    # xlsx metric: each testset id averages in (missing id -> 0), divide by 150.
    return sum(score_dict.get(i, 0.0) for i in TESTSET_IDS) / len(TESTSET_IDS)


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric = _score_records(records)
    out = [dict(r) for r in records]
    for r in out:
        r["score"] = metric
    return metric, METRIC_NAME, out
