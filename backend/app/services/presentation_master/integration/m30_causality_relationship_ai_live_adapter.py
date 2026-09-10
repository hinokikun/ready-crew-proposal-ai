"""Isolated live adapter for the frozen M30 relationship proposal contract."""

from __future__ import annotations

import json
from typing import Any, Callable, Iterable

from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, OpenAI, RateLimitError

from app.config import settings

from .m30_canonical_ai_acquisition import M30CanonicalSourceRecord
from .m30_causality_relationship_ai_proposals import (
    M30CausalityRelationshipProposalError,
    M30CausalityRelationshipProposalRequest,
    M30CausalityRelationshipAIProposal,
    build_m30_causality_relationship_proposals,
)


class M30CausalityRelationshipAILiveAdapterError(Exception):
    """Bounded adapter error that never contains node or model content."""

    def __init__(self, category: str, status_code: int = 500) -> None:
        super().__init__(category)
        self.category = category
        self.status_code = status_code


_RELATIONSHIP_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["relationships"],
    "properties": {
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["from_id", "to_id"],
                "properties": {"from_id": {"type": "string"}, "to_id": {"type": "string"}},
            },
        }
    },
}


_SYSTEM_INSTRUCTIONS = (
    "Select plausible causal edges between the supplied reviewed canonical business nodes. "
    "Return only the requested endpoint relationships using supplied node IDs. "
    "Do not invent nodes, change wording, generate evidence, source references, authority, "
    "review metadata, explanations, slide layout, Golden topology, or physical positions."
)


def build_m30_causality_relationship_ai_input(
    request: M30CausalityRelationshipProposalRequest,
) -> str:
    """Serialize only the bounded node-selection context required by the AI."""

    if not isinstance(request, M30CausalityRelationshipProposalRequest):
        raise TypeError("request must be M30CausalityRelationshipProposalRequest")
    payload = {
        "nodes": [
            {"node_id": node.candidate_id, "semantic_role": node.semantic_role, "value": node.value}
            for node in request.current_nodes
        ],
        "requested_relationship_count": request.requested_count,
        "proposal_revision": request.proposal_revision,
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
    raise M30CausalityRelationshipAILiveAdapterError("INVALID_AI_RESPONSE", 502)


def _invoke_openai(request: M30CausalityRelationshipProposalRequest) -> Any:
    if not settings.openai_api_key:
        raise M30CausalityRelationshipAILiveAdapterError("CONFIGURATION_ERROR", 400)
    client = OpenAI(api_key=settings.openai_api_key, timeout=settings.request_timeout_seconds)
    try:
        return client.responses.create(
            model=settings.openai_model,
            instructions=_SYSTEM_INSTRUCTIONS,
            input=build_m30_causality_relationship_ai_input(request),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "m30_causality_relationships",
                    "schema": _RELATIONSHIP_SCHEMA,
                    "strict": True,
                }
            },
        )
    except AuthenticationError as exc:
        raise M30CausalityRelationshipAILiveAdapterError("AI_REQUEST_FAILED", 502) from exc
    except RateLimitError as exc:
        raise M30CausalityRelationshipAILiveAdapterError("AI_REQUEST_FAILED", 429) from exc
    except APITimeoutError as exc:
        raise M30CausalityRelationshipAILiveAdapterError("AI_TIMEOUT", 504) from exc
    except APIConnectionError as exc:
        raise M30CausalityRelationshipAILiveAdapterError("AI_REQUEST_FAILED", 502) from exc
    except APIStatusError as exc:
        raise M30CausalityRelationshipAILiveAdapterError("AI_REQUEST_FAILED", exc.status_code) from exc


def propose_m30_causality_relationships_live(
    request: M30CausalityRelationshipProposalRequest,
    current_sources: Iterable[M30CanonicalSourceRecord],
    *,
    transport: Callable[[str], Any] | None = None,
) -> tuple[M30CausalityRelationshipAIProposal, ...]:
    """Make at most one live call, then delegate all semantics to the frozen builder."""

    if not isinstance(request, M30CausalityRelationshipProposalRequest):
        raise TypeError("request must be M30CausalityRelationshipProposalRequest")
    try:
        response = transport(build_m30_causality_relationship_ai_input(request)) if transport is not None else _invoke_openai(request)
    except M30CausalityRelationshipAILiveAdapterError:
        raise
    except TimeoutError as exc:
        raise M30CausalityRelationshipAILiveAdapterError("AI_TIMEOUT", 504) from exc
    except Exception as exc:
        raise M30CausalityRelationshipAILiveAdapterError("AI_REQUEST_FAILED", 502) from exc
    try:
        return build_m30_causality_relationship_proposals(request, _extract_response_text(response), current_sources)
    except M30CausalityRelationshipProposalError as exc:
        raise M30CausalityRelationshipAILiveAdapterError("OFFLINE_CONTRACT_REJECTED", 422) from exc
    except M30CausalityRelationshipAILiveAdapterError:
        raise
    except (TypeError, ValueError):
        raise M30CausalityRelationshipAILiveAdapterError("INVALID_AI_RESPONSE", 502) from None


__all__ = [
    "M30CausalityRelationshipAILiveAdapterError",
    "build_m30_causality_relationship_ai_input",
    "propose_m30_causality_relationships_live",
]
