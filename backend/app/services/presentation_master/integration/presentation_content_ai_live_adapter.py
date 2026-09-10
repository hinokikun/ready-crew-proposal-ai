"""Isolated live adapter for presentation wording proposals.

This module is deliberately not imported by the Product proposal path.  It
only connects the frozen offline contract to the existing Responses API shape.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, OpenAI, RateLimitError

from app.config import settings

from .presentation_content_ai_proposals import (
    ParsedPresentationContentAIProposal,
    PresentationContentAIProposalRequest,
    build_presentation_content_candidate,
    parse_presentation_content_ai_response,
)


class PresentationContentAIProposalError(Exception):
    """Bounded error category for the isolated presentation proposal adapter."""

    def __init__(self, category: str, status_code: int = 500) -> None:
        super().__init__(category)
        self.category = category
        self.status_code = status_code


_PRESENTATION_FIELDS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["fields"],
    "properties": {
        "fields": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["field_role", "value"],
                "properties": {"field_role": {"type": "string"}, "value": {"type": "string"}},
            },
        }
    },
}

_SYSTEM_INSTRUCTIONS = (
    "Generate presentation wording only. Preserve the supplied canonical meaning. "
    "Add no new facts, evidence, causal claims, or unsupported impact. "
    "Generate only the requested fields, using concise, clear, non-redundant business wording. "
    "Return strict JSON only in the requested schema."
)


def build_presentation_content_ai_input(request: PresentationContentAIProposalRequest) -> str:
    """Serialize only the minimum model input; system metadata is excluded."""

    if not isinstance(request, PresentationContentAIProposalRequest):
        raise TypeError("request must be PresentationContentAIProposalRequest")
    payload = {
        "semantic_role": request.semantic_role,
        "requested_field_roles": list(request.requested_field_roles),
        "canonical_sources": [
            {"semantic_role": source.semantic_role, "value": source.value}
            for source in request.source_identities
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
    raise PresentationContentAIProposalError("response_text_unavailable")


def _invoke_openai(request: PresentationContentAIProposalRequest) -> Any:
    if not settings.openai_api_key:
        raise PresentationContentAIProposalError("openai_not_configured", 400)
    client = OpenAI(api_key=settings.openai_api_key, timeout=settings.request_timeout_seconds)
    try:
        return client.responses.create(
            model=settings.openai_model,
            instructions=_SYSTEM_INSTRUCTIONS,
            input=build_presentation_content_ai_input(request),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "presentation_content_fields",
                    "schema": _PRESENTATION_FIELDS_SCHEMA,
                    "strict": True,
                }
            },
        )
    except AuthenticationError as exc:
        raise PresentationContentAIProposalError("authentication_failure", 401) from exc
    except RateLimitError as exc:
        raise PresentationContentAIProposalError("rate_limit", 429) from exc
    except APITimeoutError as exc:
        raise PresentationContentAIProposalError("timeout", 504) from exc
    except APIConnectionError as exc:
        raise PresentationContentAIProposalError("connection_failure", 502) from exc
    except APIStatusError as exc:
        raise PresentationContentAIProposalError("provider_status_failure", exc.status_code) from exc


def propose_presentation_content(
    request: PresentationContentAIProposalRequest,
    *,
    transport: Callable[[str], Any] | None = None,
) -> Any:
    """Run one isolated proposal call, then use the frozen local contracts."""

    if not isinstance(request, PresentationContentAIProposalRequest):
        raise TypeError("request must be PresentationContentAIProposalRequest")
    response = transport(build_presentation_content_ai_input(request)) if transport is not None else _invoke_openai(request)
    try:
        raw_text = _extract_response_text(response)
        parsed: ParsedPresentationContentAIProposal = parse_presentation_content_ai_response(
            raw_text, request.requested_field_roles
        )
    except PresentationContentAIProposalError:
        raise
    except (TypeError, ValueError):
        raise PresentationContentAIProposalError("invalid_structured_output") from None
    return build_presentation_content_candidate(request, parsed)


__all__ = [
    "PresentationContentAIProposalError",
    "build_presentation_content_ai_input",
    "propose_presentation_content",
]
