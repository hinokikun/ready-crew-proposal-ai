"""JSON schema helpers for Alpha Integration Review."""

from __future__ import annotations

import json
from typing import Any

from .fixtures import valid_alpha_integration_cases
from .pipeline import run_alpha_integration
from .pipeline_models import (
    AlphaEvaluationResult,
    AlphaIntegrationCase,
    AlphaIntegrationOutput,
    CrossModuleValidationResult,
)


def integration_case_input_schema() -> dict[str, Any]:
    schema = AlphaIntegrationCase.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Alpha Integration Case Input"
    schema["x-phase"] = "alpha-integration"
    return schema


def integration_case_output_schema() -> dict[str, Any]:
    schema = AlphaIntegrationOutput.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Alpha Integration Case Output"
    schema["x-phase"] = "alpha-integration"
    return schema


def integration_evaluation_schema() -> dict[str, Any]:
    schema = AlphaEvaluationResult.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Alpha Integration Evaluation"
    schema["x-phase"] = "alpha-integration"
    return schema


def cross_module_validation_schema() -> dict[str, Any]:
    schema = CrossModuleValidationResult.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Cross Module Validation"
    schema["x-phase"] = "alpha-integration"
    return schema


def phase2d_readiness_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Presentation Engine 2.0 Phase 2D Readiness",
        "type": "string",
        "enum": ["READY", "READY_WITH_LIMITATIONS", "NOT_READY", "BLOCKED"],
        "additionalProperties": False,
    }


def example_output() -> dict[str, Any]:
    return run_alpha_integration(valid_alpha_integration_cases()[0]).dict()


def invalid_examples() -> list[dict[str, Any]]:
    base = valid_alpha_integration_cases()[0].dict()
    missing_context = dict(base)
    missing_context.pop("proposal_context")
    bad_version = dict(base)
    bad_version["schema_version"] = "old"
    bad_extra = dict(base)
    bad_extra["unexpected"] = "not allowed"
    return [missing_context, bad_version, bad_extra]


def schema_json() -> str:
    return json.dumps(
        {
            "integration_case_input": integration_case_input_schema(),
            "integration_case_output": integration_case_output_schema(),
            "integration_evaluation": integration_evaluation_schema(),
            "cross_module_validation": cross_module_validation_schema(),
            "phase2d_readiness": phase2d_readiness_schema(),
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str,
    )
