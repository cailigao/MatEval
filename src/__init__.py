"""Per-task metric modules.

Each module exports:
  SLUG: str           — the data filename stem (e.g. "objective_qa")
  TITLE: str          — human-readable title for the summary table
  METRIC_NAME: str    — metric label (ACC, F1, Score, Avg, MAE)
  compute(records)    -> (metric, metric_name, scored_records)

`compute` receives the per-model records (a list of dicts) and returns
the aggregate metric, the metric name, and the per-record output list
(each output record carries a `score` field — float, None, or error string).
"""
from __future__ import annotations

import importlib
from typing import Any, Callable

SLUGS = [
    "literature_abstract_comparison",
    "experimental_plan_recommendation",
    "subjective_qa",
    "literature_based_qa",
    "device_structure_extraction",
    "experimental_parameter_extraction",
    "experimental_plan_extraction",
    "material_property_extraction",
    "result_image_analysis",
    "objective_qa",
    "experimental_safety_assessment",
    "abnormal_input_detection",
    "task_instruction_classification",
    "experimental_parameter_recommendation",
    "laboratory_instrument_call",
    "experimental_config_setting",
    "x_ray_diffraction_analysis",
    "matkg_call",
    "materials_entity_recognition",
    "microscopy_image_analysis",
    "mp_database_call",
    "aflow_database_call",
    "materials_entity_normalization",
    "synthesis_action_retrieval",
]

_MODULES: dict[str, Any] = {}


def _load(slug: str):
    if slug not in _MODULES:
        _MODULES[slug] = importlib.import_module(f"src.{slug}")
    return _MODULES[slug]


def get_compute(slug: str) -> Callable:
    return _load(slug).compute


def get_title(slug: str) -> str:
    return _load(slug).TITLE


def get_metric_name(slug: str) -> str:
    return _load(slug).METRIC_NAME
