"""Task-Instruction Classification: per-record ACC."""
from __future__ import annotations

from src.common import compute_per_record, extract_json_from_answer

SLUG = "task_instruction_classification"
TITLE = "Task-Instruction Classification"
METRIC_NAME = "ACC"
SCALE = 1.0

TASKS_DICT_INSTRUCTION = {
    "1": "Materials Objective QA",
    "2": "Materials Subjective QA",
    "3": "Materials Named Entity Recognition",
    "4": "Materials Named Entity Normalization",
    "5": "Material Property Extraction",
    "6": "Synthesis Action Retrieval",
    "7": "Device Structure Extraction",
    "8": "Experimental Parameter Extraction",
    "9": "Experimental Procedure Extraction",
    "10": "Document-grounded QA",
    "11": "Abstract Comparison",
    "12": "MP Database Query",
    "13": "Aflow Database Query",
    "14": "MatKG Knowledge Graph Query",
    "15": "Experimental Parameter Recommendation",
    "16": "Experimental Procedure Recommendation",
    "17": "Experimental Safety Boundary Annotation",
    "18": "Experimental Config Package Generation",
    "19": "Experimental Device Invocation",
}


def score(r: dict) -> float | None:
    if not r.get("answer"):
        return 0.0
    parsed = extract_json_from_answer(r["answer"])
    if not isinstance(parsed, dict):
        return None
    task_id = str(parsed.get("task_id", ""))
    task_name = parsed.get("task_name", "")
    if task_id not in TASKS_DICT_INSTRUCTION or task_name != TASKS_DICT_INSTRUCTION[task_id]:
        return 0.0
    return 1.0 if task_name == r.get("target") else 0.0


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
