"""Generic, reviewed presentation content ready for a later slot binder."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
import unicodedata

from .production_semantic_contract import SemanticAuthority, SemanticReviewState


class SlotReadyDerivationType(str, Enum):
    DIRECT = "DIRECT"
    LOSSLESS_TRANSFORMATION = "LOSSLESS_TRANSFORMATION"
    SEMANTIC_DERIVATION = "SEMANTIC_DERIVATION"


@dataclass(frozen=True)
class SlotReadySourceIdentity:
    source_item_id: str
    semantic_role: str
    value: str


@dataclass(frozen=True)
class SlotReadyField:
    field_role: str
    value: str
    # Optional for legacy homogeneous content; required on every field when
    # a content object uses field-level provenance.
    derivation_type: SlotReadyDerivationType | str | None = None
    authority: SemanticAuthority | str | None = None
    review_state: SemanticReviewState | str | None = None
    confirmation_authority: SemanticAuthority | str | None = None


@dataclass(frozen=True)
class SlotReadyContent:
    content_id: str
    source_item_id: str
    semantic_role: str
    fields: tuple[SlotReadyField, ...]
    derivation_type: SlotReadyDerivationType | str | None
    review_state: SemanticReviewState | str | None
    source_fingerprint: str
    confirmation_authority: SemanticAuthority | str | None = None


_FINGERPRINT_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _normalize_source_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).strip().split())


def compute_source_fingerprint(source_identity: SlotReadySourceIdentity) -> str:
    """Hash only canonical source identity using deterministic UTF-8 JSON."""

    if not isinstance(source_identity, SlotReadySourceIdentity):
        raise TypeError("source_identity must be a SlotReadySourceIdentity")
    if not source_identity.source_item_id.strip() or not source_identity.semantic_role.strip() or not source_identity.value.strip():
        raise ValueError("source identity fields are required")
    payload = {
        "source_item_id": _normalize_source_text(source_identity.source_item_id),
        "semantic_role": _normalize_source_text(source_identity.semantic_role),
        "value": _normalize_source_text(source_identity.value),
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_slot_ready_content(content: SlotReadyContent) -> tuple[str, ...]:
    """Return bounded validation failures; never performs I/O or transformation."""

    errors: list[str] = []
    if not isinstance(content, SlotReadyContent):
        return ("content must be SlotReadyContent",)
    if not content.content_id.strip():
        errors.append("content_id is required")
    if not content.source_item_id.strip():
        errors.append("source_item_id is required")
    if not content.semantic_role.strip():
        errors.append("semantic_role is required")
    if not _FINGERPRINT_PATTERN.fullmatch(content.source_fingerprint):
        errors.append("source_fingerprint must be 64 lowercase hexadecimal characters")

    if content.derivation_type is None:
        derivation = None
    else:
        try:
            derivation = SlotReadyDerivationType(content.derivation_type)
        except (TypeError, ValueError):
            derivation = None
            errors.append("unsupported derivation type")

    if content.review_state is None:
        review_state = None
    else:
        try:
            review_state = SemanticReviewState(content.review_state)
        except (TypeError, ValueError):
            review_state = None
            errors.append("unsupported review state")

    authority = content.confirmation_authority
    if authority is not None:
        try:
            authority = SemanticAuthority(authority)
        except (TypeError, ValueError):
            errors.append("malformed confirmation authority")
            authority = None
        if authority is not None and authority != SemanticAuthority.USER_EXPLICIT:
            errors.append("confirmation authority must be USER_EXPLICIT")

    if not content.fields:
        errors.append("at least one field is required")
    field_roles: set[str] = set()
    field_derivations: list[SlotReadyDerivationType | None] = []
    field_metadata_present: list[bool] = []
    for field in content.fields:
        if not isinstance(field, SlotReadyField):
            errors.append("malformed slot-ready field")
            continue
        role = field.field_role.strip()
        if not role:
            errors.append("field_role is required")
        elif role in field_roles:
            errors.append(f"duplicate field role: {role}")
        else:
            field_roles.add(role)
        if not field.value.strip():
            errors.append(f"field value is required: {role or '<empty>'}")

        field_derivation = None
        if field.derivation_type is not None:
            try:
                field_derivation = SlotReadyDerivationType(field.derivation_type)
            except (TypeError, ValueError):
                errors.append(f"unsupported field derivation type: {role or '<empty>'}")
        field_derivations.append(field_derivation)
        field_metadata_present.append(field.derivation_type is not None)

        if field.authority is not None:
            try:
                field_authority = SemanticAuthority(field.authority)
            except (TypeError, ValueError):
                errors.append(f"malformed field authority: {role or '<empty>'}")
                field_authority = None
        else:
            field_authority = None
        if field.review_state is not None:
            try:
                field_review = SemanticReviewState(field.review_state)
            except (TypeError, ValueError):
                errors.append(f"unsupported field review state: {role or '<empty>'}")
                field_review = None
        else:
            field_review = None
        if field.confirmation_authority is not None:
            try:
                field_confirmation = SemanticAuthority(field.confirmation_authority)
            except (TypeError, ValueError):
                errors.append(f"malformed field confirmation authority: {role or '<empty>'}")
                field_confirmation = None
            if field_confirmation is not None and field_confirmation != SemanticAuthority.USER_EXPLICIT:
                errors.append(f"field confirmation authority must be USER_EXPLICIT: {role or '<empty>'}")
        else:
            field_confirmation = None
        if field_derivation in {SlotReadyDerivationType.LOSSLESS_TRANSFORMATION, SlotReadyDerivationType.SEMANTIC_DERIVATION}:
            if field_authority != SemanticAuthority.USER_EXPLICIT:
                errors.append(f"derived field requires USER_EXPLICIT authority: {role or '<empty>'}")
            if field_review not in {SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED}:
                errors.append(f"derived field requires CONFIRMED or CORRECTED review: {role or '<empty>'}")
            if field_confirmation != SemanticAuthority.USER_EXPLICIT:
                errors.append(f"derived field requires Human confirmation: {role or '<empty>'}")

    field_level_mode = any(field_metadata_present)
    if field_level_mode and not all(field_metadata_present):
        errors.append("field derivation metadata must be complete for mixed content")
    if field_level_mode and content.derivation_type is not None:
        errors.append("field-level provenance requires no object-level derivation summary")
    if field_level_mode and content.review_state is not None:
        errors.append("field-level provenance requires no object-level review summary")
    if field_level_mode and content.confirmation_authority is not None:
        errors.append("field-level provenance requires no object-level confirmation summary")

    if not field_level_mode:
        if review_state not in {SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED}:
            errors.append("slot-ready content requires CONFIRMED or CORRECTED review")
        if derivation in {SlotReadyDerivationType.LOSSLESS_TRANSFORMATION, SlotReadyDerivationType.SEMANTIC_DERIVATION} and authority != SemanticAuthority.USER_EXPLICIT:
            errors.append("derived slot-ready content requires USER_EXPLICIT authority")
    return tuple(dict.fromkeys(errors))


def is_slot_ready_admissible(content: SlotReadyContent) -> bool:
    """Return whether content is safe for a future downstream binding boundary."""

    return not validate_slot_ready_content(content)


def validate_slot_ready_against_source(
    content: SlotReadyContent,
    current_source_identity: SlotReadySourceIdentity,
) -> tuple[str, ...]:
    """Validate stored SlotReadyContent against the current canonical source."""

    errors = list(validate_slot_ready_content(content))
    try:
        current_fingerprint = compute_source_fingerprint(current_source_identity)
    except (TypeError, ValueError) as exc:
        errors.append(str(exc))
        return tuple(dict.fromkeys(errors))
    if content.source_item_id != current_source_identity.source_item_id:
        errors.append("source_item_id does not match current source")
    if content.semantic_role != current_source_identity.semantic_role:
        errors.append("semantic_role does not match current source")
    if content.source_fingerprint != current_fingerprint:
        errors.append("source fingerprint mismatch")
    return tuple(dict.fromkeys(errors))


__all__ = [
    "SlotReadyContent",
    "SlotReadyDerivationType",
    "SlotReadyField",
    "SlotReadySourceIdentity",
    "compute_source_fingerprint",
    "is_slot_ready_admissible",
    "validate_slot_ready_against_source",
    "validate_slot_ready_content",
]
