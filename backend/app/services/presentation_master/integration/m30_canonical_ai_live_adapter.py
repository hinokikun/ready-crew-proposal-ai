"""Isolated live adapter for the frozen M30 canonical AI contract."""

from __future__ import annotations

import json
from typing import Any, Callable

from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, OpenAI, RateLimitError

from app.config import settings

from .m30_canonical_ai_acquisition import (
    M30CanonicalAcquisitionError,
    M30CanonicalAcquisitionRequest,
    M30CanonicalAIProposalCandidate,
    build_m30_canonical_ai_proposals,
)


class M30CanonicalAILiveAdapterError(Exception):
    """Bounded adapter error that never includes source or model content."""

    def __init__(self, category: str, status_code: int = 500) -> None:
        super().__init__(category)
        self.category = category
        self.status_code = status_code


_CANONICAL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["items"],
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["semantic_role", "value"],
                "properties": {"semantic_role": {"type": "string"}, "value": {"type": "string"}},
            },
        }
    },
}

_SYSTEM_INSTRUCTIONS = (
    "Propose business semantics for later Human review. This is not presentation copy. "
    "Return only the requested semantic role and count as strict JSON. "
    "Do not invent evidence, source references, authority, review state, or provenance. "
    "Do not mention Golden, iceberg, center, peripheral, slide, layout, slot, or physical position. "
    "For causal_state, describe an intermediate business or operational state."
)


def build_m30_canonical_ai_input(request: M30CanonicalAcquisitionRequest) -> str:
    """Serialize only the bounded canonical acquisition request."""

    if not isinstance(request, M30CanonicalAcquisitionRequest):
        raise TypeError("request must be M30CanonicalAcquisitionRequest")
    payload = {
        "semantic_role": request.semantic_role,
        "requested_count": request.requested_count,
        "acquisition_revision": request.acquisition_revision,
        "source_context": [
            {
                "source_id": source.source_id,
                "source_field": source.source_field,
                "value": source.value,
                "source_reference": source.source_reference,
            }
            for source in request.source_records
        ],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


def _extract_response_text(response: Any) -> str:
    if isinstance(response, str):
        return response
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text:
        return output_text
    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            value = getattr(content, "text", None)
            if isinstance(value, str):
                chunks.append(value)
    if chunks:
        return "".join(chunks)
    raise M30CanonicalAILiveAdapterError("INVALID_AI_RESPONSE", 502)


def _invoke_openai(request: M30CanonicalAcquisitionRequest) -> Any:
    if not settings.openai_api_key:
        raise M30CanonicalAILiveAdapterError("CONFIGURATION_ERROR", 400)
    client = OpenAI(api_key=settings.openai_api_key, timeout=settings.request_timeout_seconds)
    try:
        return client.responses.create(
            model=settings.openai_model,
            instructions=_SYSTEM_INSTRUCTIONS,
            input=build_m30_canonical_ai_input(request),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "m30_canonical_semantics",
                    "schema": _CANONICAL_SCHEMA,
                    "strict": True,
                }
            },
        )
    except AuthenticationError as exc:
        raise M30CanonicalAILiveAdapterError("AI_REQUEST_FAILED", 502) from exc
    except RateLimitError as exc:
        raise M30CanonicalAILiveAdapterError("AI_REQUEST_FAILED", 429) from exc
    except APITimeoutError as exc:
        raise M30CanonicalAILiveAdapterError("AI_TIMEOUT", 504) from exc
    except APIConnectionError as exc:
        raise M30CanonicalAILiveAdapterError("AI_REQUEST_FAILED", 502) from exc
    except APIStatusError as exc:
        raise M30CanonicalAILiveAdapterError("AI_REQUEST_FAILED", exc.status_code) from exc


def propose_m30_canonical_live(
    request: M30CanonicalAcquisitionRequest,
    *,
    transport: Callable[[str], Any] | None = None,
) -> tuple[M30CanonicalAIProposalCandidate, ...]:
    """Make at most one bounded AI call and delegate parsing/building offline."""

    if not isinstance(request, M30CanonicalAcquisitionRequest):
        raise TypeError("request must be M30CanonicalAcquisitionRequest")
    try:
        response = transport(build_m30_canonical_ai_input(request)) if transport is not None else _invoke_openai(request)
    except M30CanonicalAILiveAdapterError:
        raise
    except TimeoutError as exc:
        raise M30CanonicalAILiveAdapterError("AI_TIMEOUT", 504) from exc
    except Exception as exc:
        raise M30CanonicalAILiveAdapterError("AI_REQUEST_FAILED", 502) from exc
    try:
        return build_m30_canonical_ai_proposals(request, _extract_response_text(response))
    except M30CanonicalAcquisitionError as exc:
        raise M30CanonicalAILiveAdapterError("OFFLINE_CONTRACT_REJECTED", 422) from exc
    except M30CanonicalAILiveAdapterError:
        raise
    except (TypeError, ValueError):
        raise M30CanonicalAILiveAdapterError("INVALID_AI_RESPONSE", 502) from None


__all__ = [
    "M30CanonicalAILiveAdapterError",
    "build_m30_canonical_ai_input",
    "propose_m30_canonical_live",
]
