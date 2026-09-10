"""Pure offline contract for proposing canonical M30 business semantics.

This module deliberately has no API, prompt, network, or AI-client dependency.
It validates a bounded request, parses strict structured output supplied by a
future adapter, and labels every result as an unconfirmed AI proposal.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import unicodedata
from typing import Any, Iterable

from .production_semantic_contract import (
    ProductionSemanticCandidate,
    SemanticAuthority,
    SemanticReviewState,
)


M30_CANONICAL_ROLES = (
    "visible_issue",
    "root_cause",
    "causal_state",
    "business_implication",
    "solution_direction",
)
M30_CANONICAL_MAX_COUNTS = {
    "visible_issue": 1,
    "root_cause": 4,
    "causal_state": 5,
    "business_implication": 4,
    "solution_direction": 1,
}
_PHYSICAL_STATE_TERMS = frozenset({"center", "peripheral", "left", "right", "top", "bottom", "iceberg"})
_SOURCE_FINGERPRINT_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class M30CanonicalAcquisitionError(ValueError):
    """Bounded error category safe for a future Product/API boundary."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


@dataclass(frozen=True)
class M30CanonicalSourceRecord:
    """One real, bounded source record available to the proposal adapter."""

    source_id: str
    source_field: str
    value: str
    source_reference: str

    def __post_init__(self) -> None:
        if not all(isinstance(item, str) and item.strip() for item in (self.source_id, self.source_field, self.value, self.source_reference)):
            raise M30CanonicalAcquisitionError("INVALID_SOURCE")


@dataclass(frozen=True)
class M30CanonicalSourceIdentity:
    """Immutable provenance identity retained for later currentness checks."""

    source_id: str
    source_field: str
    source_reference: str

    def __post_init__(self) -> None:
        if not all(isinstance(item, str) and item.strip() for item in (self.source_id, self.source_field, self.source_reference)):
            raise M30CanonicalAcquisitionError("INVALID_SOURCE")


@dataclass(frozen=True)
class M30CanonicalAcquisitionRequest:
    """Bounded source context and one missing canonical role/count request."""

    semantic_role: str
    requested_count: int
    source_records: tuple[M30CanonicalSourceRecord, ...]
    acquisition_revision: str = "v1"
    existing_reviewed_candidates: tuple[ProductionSemanticCandidate, ...] = ()

    def __post_init__(self) -> None:
        if self.semantic_role not in M30_CANONICAL_ROLES:
            raise M30CanonicalAcquisitionError("INVALID_ROLE")
        maximum = M30_CANONICAL_MAX_COUNTS[self.semantic_role]
        if not isinstance(self.requested_count, int) or self.requested_count <= 0 or self.requested_count > maximum:
            raise M30CanonicalAcquisitionError("INVALID_COUNT")
        if not self.source_records or any(not isinstance(record, M30CanonicalSourceRecord) for record in self.source_records):
            raise M30CanonicalAcquisitionError("INVALID_SOURCE")
        if len({record.source_id for record in self.source_records}) != len(self.source_records):
            raise M30CanonicalAcquisitionError("INVALID_SOURCE")
        if not isinstance(self.acquisition_revision, str) or not self.acquisition_revision.strip():
            raise M30CanonicalAcquisitionError("INVALID_REQUEST")
        if any(not isinstance(candidate, ProductionSemanticCandidate) for candidate in self.existing_reviewed_candidates):
            raise M30CanonicalAcquisitionError("INVALID_REQUEST")


@dataclass(frozen=True)
class M30CanonicalAIProposalCandidate:
    candidate_id: str
    semantic_role: str
    value: str
    source_type: str
    source_field: str
    source_reference: str
    source_references: tuple[str, ...]
    source_identities: tuple[M30CanonicalSourceIdentity, ...]
    source_fingerprint: str
    authority: SemanticAuthority
    review_state: SemanticReviewState
    confirmation_authority: SemanticAuthority | None
    inferred: bool
    acquisition_revision: str
    original_candidate_id: str | None = None


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).strip().casefold().split())


def _normalize_source_component(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).strip().split())


def compute_m30_canonical_source_fingerprint(
    source_records: Iterable[M30CanonicalSourceRecord],
) -> str:
    """Hash ordered source identity and value without retaining raw values."""

    records = tuple(source_records)
    if not records or any(not isinstance(record, M30CanonicalSourceRecord) for record in records):
        raise M30CanonicalAcquisitionError("INVALID_SOURCE")
    identities = [(record.source_id, record.source_field, record.source_reference) for record in records]
    if len(set(identities)) != len(identities):
        raise M30CanonicalAcquisitionError("INVALID_SOURCE")
    canonical = [
        {
            "source_id": _normalize_source_component(record.source_id),
            "source_field": _normalize_source_component(record.source_field),
            "source_reference": _normalize_source_component(record.source_reference),
            "value": _normalize_source_component(record.value),
        }
        for record in records
    ]
    encoded = json.dumps(canonical, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_m30_canonical_candidate_current_sources(
    candidate: M30CanonicalAIProposalCandidate,
    current_sources: Iterable[M30CanonicalSourceRecord],
) -> bool:
    """Return true only when stored ordered provenance and current sources match."""

    if not isinstance(candidate, M30CanonicalAIProposalCandidate):
        return False
    stored_identities = getattr(candidate, "source_identities", None)
    stored_fingerprint = getattr(candidate, "source_fingerprint", None)
    if not isinstance(stored_identities, tuple) or not stored_identities:
        return False
    if any(not isinstance(identity, M30CanonicalSourceIdentity) for identity in stored_identities):
        return False
    if len({(item.source_id, item.source_field, item.source_reference) for item in stored_identities}) != len(stored_identities):
        return False
    if not isinstance(stored_fingerprint, str) or not _SOURCE_FINGERPRINT_PATTERN.fullmatch(stored_fingerprint):
        return False
    try:
        current = tuple(current_sources)
        if not current or any(not isinstance(record, M30CanonicalSourceRecord) for record in current):
            return False
        current_identities = tuple(M30CanonicalSourceIdentity(record.source_id, record.source_field, record.source_reference) for record in current)
        if len({(item.source_id, item.source_field, item.source_reference) for item in current_identities}) != len(current_identities):
            return False
        if stored_identities != current_identities:
            return False
        return stored_fingerprint == compute_m30_canonical_source_fingerprint(current)
    except (TypeError, M30CanonicalAcquisitionError):
        return False


def _candidate_id(request: M30CanonicalAcquisitionRequest, ordinal: int) -> str:
    identity = {
        "semantic_role": request.semantic_role,
        "source_ids": [record.source_id for record in request.source_records],
        "source_fields": [record.source_field for record in request.source_records],
        "acquisition_revision": request.acquisition_revision,
        "ordinal": ordinal,
    }
    encoded = json.dumps(identity, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return f"m30-canonical-ai:{hashlib.sha256(encoded).hexdigest()}"


def _validate_value(value: Any, role: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise M30CanonicalAcquisitionError("EMPTY_VALUE")
    normalized = _normalized(value)
    if role == "causal_state" and any(term in normalized.split() for term in _PHYSICAL_STATE_TERMS):
        raise M30CanonicalAcquisitionError("INVALID_STRUCTURED_OUTPUT")
    return value.strip()


def parse_m30_canonical_ai_response(
    raw_response: str,
    request: M30CanonicalAcquisitionRequest,
) -> tuple[str, ...]:
    """Parse exactly ``{"items":[{"semantic_role","value"}]}`` JSON."""

    if not isinstance(raw_response, str):
        raise M30CanonicalAcquisitionError("INVALID_STRUCTURED_OUTPUT")
    try:
        payload: Any = json.loads(raw_response)
    except (TypeError, json.JSONDecodeError) as exc:
        raise M30CanonicalAcquisitionError("INVALID_STRUCTURED_OUTPUT") from exc
    if not isinstance(payload, dict) or set(payload) != {"items"} or not isinstance(payload["items"], list):
        raise M30CanonicalAcquisitionError("INVALID_STRUCTURED_OUTPUT")
    if len(payload["items"]) != request.requested_count:
        raise M30CanonicalAcquisitionError("INVALID_COUNT")
    values: list[str] = []
    for item in payload["items"]:
        if not isinstance(item, dict) or set(item) != {"semantic_role", "value"}:
            raise M30CanonicalAcquisitionError("INVALID_STRUCTURED_OUTPUT")
        if item["semantic_role"] != request.semantic_role:
            raise M30CanonicalAcquisitionError("INVALID_ROLE")
        values.append(_validate_value(item["value"], request.semantic_role))
    normalized_values = [_normalized(value) for value in values]
    if len(set(normalized_values)) != len(normalized_values):
        raise M30CanonicalAcquisitionError("DUPLICATE_VALUE")
    return tuple(values)


def build_m30_canonical_ai_proposals(
    request: M30CanonicalAcquisitionRequest,
    raw_response: str,
) -> tuple[M30CanonicalAIProposalCandidate, ...]:
    """Build non-admissible AI candidates from strict structured output."""

    values = parse_m30_canonical_ai_response(raw_response, request)
    source_references = tuple(record.source_reference for record in request.source_records)
    source_fields = tuple(record.source_field for record in request.source_records)
    source_identities = tuple(
        M30CanonicalSourceIdentity(record.source_id, record.source_field, record.source_reference)
        for record in request.source_records
    )
    source_fingerprint = compute_m30_canonical_source_fingerprint(request.source_records)
    return tuple(
        M30CanonicalAIProposalCandidate(
            candidate_id=_candidate_id(request, ordinal),
            semantic_role=request.semantic_role,
            value=value,
            source_type="bounded_source_context",
            source_field="|".join(source_fields),
            source_reference="|".join(source_references),
            source_references=source_references,
            source_identities=source_identities,
            source_fingerprint=source_fingerprint,
            authority=SemanticAuthority.AI_PROPOSED,
            review_state=SemanticReviewState.UNCONFIRMED,
            confirmation_authority=None,
            inferred=True,
            acquisition_revision=request.acquisition_revision,
        )
        for ordinal, value in enumerate(values)
    )


__all__ = [
    "M30_CANONICAL_MAX_COUNTS",
    "M30_CANONICAL_ROLES",
    "M30CanonicalAcquisitionError",
    "M30CanonicalAcquisitionRequest",
    "M30CanonicalAIProposalCandidate",
    "M30CanonicalSourceRecord",
    "M30CanonicalSourceIdentity",
    "build_m30_canonical_ai_proposals",
    "compute_m30_canonical_source_fingerprint",
    "parse_m30_canonical_ai_response",
    "validate_m30_canonical_candidate_current_sources",
]
