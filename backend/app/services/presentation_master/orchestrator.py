from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from app.models import PptxDownloadRequest

from .contracts import (
    MASTER_FEATURE_FLAG,
    MASTER_SOURCE_OF_TRUTH,
    MASTER_VERSION,
    MasterBuildOutput,
    MasterQualityError,
    MasterUnsupportedInput,
)
from .grammar import grammar_contract_summary
from .qa import route_payload_for_master, validate_master_output


CoreBuilder = Callable[[PptxDownloadRequest], Any]


def build_presentation_master(
    payload: PptxDownloadRequest,
    *,
    core_builder: CoreBuilder,
    request_id: str | None = None,
    project_id: str | None = None,
) -> MasterBuildOutput:
    started = perf_counter()
    route = route_payload_for_master(payload)
    if not route.supported:
        raise MasterUnsupportedInput(route)

    core_result = core_builder(payload)
    quality_report = dict(core_result.quality_report or {})
    qa_report = validate_master_output(payload, core_result.pptx_bytes, quality_report)
    if qa_report["blocking"]:
        raise MasterQualityError("master_runtime_qa_blocked", qa_report=qa_report)

    quality_report.update(
        {
            "requested_version": MASTER_VERSION,
            "actual_version": MASTER_VERSION,
            "fallback_used": False,
            "fallback_reason": "",
            "feature_flag": MASTER_FEATURE_FLAG,
            "request_id": request_id or "",
            "project_id": project_id or "",
            "generation_time_ms": round((perf_counter() - started) * 1000),
            "production_native_module": "app.services.presentation_master",
            "candidate_source_of_truth": MASTER_SOURCE_OF_TRUTH,
            "visual_logic_duplication": 0,
            "artifact_runtime_dependency": False,
            "engine_requested": MASTER_VERSION,
            "engine_used": MASTER_VERSION,
            "mode": "enabled",
            "qa_result": qa_report["status"],
            "summary_or_normal": "summary" if payload.summary else "normal",
            "master_route": route.to_dict(),
            "phase4c_grammar_contract": grammar_contract_summary(),
            "master_qa": qa_report,
        }
    )
    return MasterBuildOutput(pptx_bytes=core_result.pptx_bytes, quality_report=quality_report)
