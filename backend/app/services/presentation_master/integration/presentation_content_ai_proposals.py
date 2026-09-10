"""Pure offline boundary for AI-proposed presentation wording."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .presentation_content_candidates import (
    PresentationContentCandidate,
    PresentationContentField,
    PresentationContentSourceIdentity,
    compute_presentation_content_fingerprint,
)
from .slot_ready_content import SlotReadyDerivationType
from .production_semantic_contract import SemanticAuthority, SemanticReviewState


@dataclass(frozen=True)
class PresentationContentAIProposalRequest:
    semantic_role: str
    source_identities: tuple[PresentationContentSourceIdentity, ...]
    requested_field_roles: tuple[str, ...]
    proposal_revision: str

    def __post_init__(self) -> None:
        if not isinstance(self.semantic_role, str) or not self.semantic_role.strip():
            raise ValueError("semantic_role is required")
        if not self.source_identities:
            raise ValueError("source_identities are required")
        if not self.requested_field_roles:
            raise ValueError("requested_field_roles are required")
        if not isinstance(self.proposal_revision, str) or not self.proposal_revision.strip():
            raise ValueError("proposal_revision is required")
        if any(not isinstance(role, str) or not role.strip() for role in self.requested_field_roles):
            raise ValueError("requested field roles must be non-empty strings")
        if len(set(self.requested_field_roles)) != len(self.requested_field_roles):
            raise ValueError("requested field roles must be unique")
        if any(not isinstance(source, PresentationContentSourceIdentity) for source in self.source_identities):
            raise TypeError("source identities must use the existing source identity contract")
        if len({source.source_item_id for source in self.source_identities}) != len(self.source_identities):
            raise ValueError("source identities must not duplicate source_item_id")
        compute_presentation_content_fingerprint(self.source_identities)


@dataclass(frozen=True)
class ParsedPresentationContentAIProposal:
    fields: tuple[PresentationContentField, ...]


def _candidate_id(request: PresentationContentAIProposalRequest) -> str:
    source_fingerprint = compute_presentation_content_fingerprint(request.source_identities)
    identity = {
        "semantic_role": request.semantic_role,
        "source_fingerprint": source_fingerprint,
        "requested_field_roles": list(request.requested_field_roles),
        "proposal_revision": request.proposal_revision,
    }
    encoded = json.dumps(identity, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return f"presentation-ai:{hashlib.sha256(encoded).hexdigest()}"


def parse_presentation_content_ai_response(
    raw_response: str,
    requested_field_roles: tuple[str, ...],
) -> ParsedPresentationContentAIProposal:
    """Parse exactly the requested field/value JSON contract, fail closed."""

    if not isinstance(raw_response, str):
        raise ValueError("AI response must be a JSON string")
    if not isinstance(requested_field_roles, tuple) or not requested_field_roles:
        raise ValueError("requested field roles are required")
    if any(not isinstance(role, str) or not role.strip() for role in requested_field_roles):
        raise ValueError("requested field roles must be non-empty strings")
    if len(set(requested_field_roles)) != len(requested_field_roles):
        raise ValueError("requested field roles must be unique")
    try:
        payload: Any = json.loads(raw_response)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("AI response must be strict JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"fields"}:
        raise ValueError("AI response must contain only the fields key")
    entries = payload["fields"]
    if not isinstance(entries, list):
        raise ValueError("fields must be an array")
    parsed: dict[str, PresentationContentField] = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"field_role", "value"}:
            raise ValueError("field entry keys are invalid")
        role = entry["field_role"]
        value = entry["value"]
        if not isinstance(role, str) or not role.strip():
            raise ValueError("field_role must be a non-empty string")
        if not isinstance(value, str) or not value.strip():
            raise ValueError("value must be a non-empty string")
        if role in parsed:
            raise ValueError("duplicate returned field role")
        parsed[role] = PresentationContentField(role, value)
    if set(parsed) != set(requested_field_roles):
        raise ValueError("returned fields must exactly match requested fields")
    return ParsedPresentationContentAIProposal(tuple(parsed[role] for role in requested_field_roles))


def build_presentation_content_candidate(
    request: PresentationContentAIProposalRequest,
    parsed_result: ParsedPresentationContentAIProposal,
) -> PresentationContentCandidate:
    """Build a non-admissible AI proposal with metadata owned by the system."""

    if not isinstance(request, PresentationContentAIProposalRequest):
        raise TypeError("request must be PresentationContentAIProposalRequest")
    if not isinstance(parsed_result, ParsedPresentationContentAIProposal):
        raise TypeError("parsed_result must be ParsedPresentationContentAIProposal")
    if tuple(field.field_role for field in parsed_result.fields) != request.requested_field_roles:
        raise ValueError("parsed fields must match request order")
    source_fingerprint = compute_presentation_content_fingerprint(request.source_identities)
    return PresentationContentCandidate(
        candidate_id=_candidate_id(request),
        semantic_role=request.semantic_role,
        fields=parsed_result.fields,
        source_identities=request.source_identities,
        source_fingerprint=source_fingerprint,
        derivation_type=SlotReadyDerivationType.SEMANTIC_DERIVATION,
        authority=SemanticAuthority.AI_PROPOSED,
        review_state=SemanticReviewState.UNCONFIRMED,
        confirmation_authority=None,
    )


__all__ = [
    "ParsedPresentationContentAIProposal",
    "PresentationContentAIProposalRequest",
    "build_presentation_content_candidate",
    "parse_presentation_content_ai_response",
]
