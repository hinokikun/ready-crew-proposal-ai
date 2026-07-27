"""Validators for Phase 2C message designs."""

from __future__ import annotations

import re
from typing import Any, Iterable

from pydantic import ValidationError as PydanticValidationError

from .designer_contracts import (
    AMBIGUOUS_LANGUAGE,
    INTERNAL_LABEL_PATTERNS,
    MESSAGE_LENGTH_LIMITS,
    NOUN_ONLY_HEADLINES,
    PLACEHOLDER_LABELS,
    WEAK_LANGUAGE,
)
from .designer_enums import EvidenceAlignmentLevel, MessageStatus, MessageValidationSeverity
from .designer_errors import MessageErrorCode, SUPPORTED_MESSAGE_DESIGN_VERSION, SUPPORTED_MESSAGE_DESIGNER_OUTPUT_VERSION
from .designer_models import (
    MessageDesignerOutput,
    MessageValidationIssue,
    MessageValidationResult,
    SlideMessageDesign,
)
from .designer_normalizers import normalize_message_designer_output_dict, normalize_slide_message_design_dict


def _issue(
    code: str,
    severity: MessageValidationSeverity,
    field_path: str,
    message: str,
    suggestion: str,
    *,
    blocking: bool | None = None,
    source: str = "message_validator",
    related_slide_id: str | None = None,
    related_evidence_ids: list[str] | None = None,
) -> MessageValidationIssue:
    return MessageValidationIssue(
        code=code,
        severity=severity,
        field_path=field_path,
        message=message,
        suggestion=suggestion,
        blocking=severity == MessageValidationSeverity.ERROR if blocking is None else blocking,
        source=source,
        related_slide_id=related_slide_id,
        related_evidence_ids=related_evidence_ids or [],
    )


def _pydantic_issues(error: PydanticValidationError) -> list[MessageValidationIssue]:
    issues: list[MessageValidationIssue] = []
    for item in error.errors():
        field_path = ".".join(str(part) for part in item.get("loc", ("payload",)))
        err_type = str(item.get("type", ""))
        code = MessageErrorCode.SCHEMA_REQUIRED
        if "enum" in err_type:
            code = MessageErrorCode.SCHEMA_ENUM
        elif "extra" in err_type:
            code = MessageErrorCode.SCHEMA_EXTRA
        elif field_path.startswith("numeric_claims"):
            code = MessageErrorCode.NUMERIC_UNSUPPORTED
        elif field_path == "headline":
            code = MessageErrorCode.HEADLINE_LENGTH
        elif field_path == "main_message":
            code = MessageErrorCode.MAIN_LENGTH
        elif field_path.startswith("supporting_messages"):
            code = MessageErrorCode.SUPPORT_LENGTH
        issues.append(
            _issue(
                code,
                MessageValidationSeverity.ERROR,
                field_path,
                str(item.get("msg", "Invalid message design field.")),
                "Fix the field so it matches the Message Designer schema.",
                source="schema",
            )
        )
    return issues


def _contains_any(text: str, terms: Iterable[str]) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for term in terms:
        needle = term.lower()
        if needle and needle in lower:
            found.append(term)
    return found


def _has_digits(text: str) -> bool:
    return bool(re.search(r"\d", text))


def _all_text(design: SlideMessageDesign) -> str:
    parts = [
        design.headline,
        design.main_message,
        design.key_takeaway,
        design.speaker_note_summary,
        *[item.text for item in design.supporting_messages],
    ]
    return " ".join(parts)


def _validate_lengths(design: SlideMessageDesign, issues: list[MessageValidationIssue]) -> None:
    if len(design.headline) > MESSAGE_LENGTH_LIMITS["headline"]:
        issues.append(_issue(MessageErrorCode.HEADLINE_LENGTH, MessageValidationSeverity.ERROR, "headline", "Headline is too long.", "Keep headline within 60 characters.", related_slide_id=design.slide_blueprint_id))
    if len(design.main_message) > MESSAGE_LENGTH_LIMITS["main_message"]:
        issues.append(_issue(MessageErrorCode.MAIN_LENGTH, MessageValidationSeverity.ERROR, "main_message", "Main message is too long.", "Keep main message within 120 characters.", related_slide_id=design.slide_blueprint_id))
    if len(design.supporting_messages) > MESSAGE_LENGTH_LIMITS["supporting_messages"]:
        issues.append(_issue(MessageErrorCode.SUPPORT_COUNT, MessageValidationSeverity.ERROR, "supporting_messages", "Too many supporting messages.", "Use at most three supporting messages.", related_slide_id=design.slide_blueprint_id))
    for index, item in enumerate(design.supporting_messages):
        if len(item.text) > MESSAGE_LENGTH_LIMITS["supporting_message"]:
            issues.append(_issue(MessageErrorCode.SUPPORT_LENGTH, MessageValidationSeverity.ERROR, f"supporting_messages[{index}].text", "Supporting message is too long.", "Keep each supporting message within 80 characters.", related_slide_id=design.slide_blueprint_id))


def _validate_message_quality(design: SlideMessageDesign, issues: list[MessageValidationIssue]) -> None:
    if not design.headline.strip():
        issues.append(_issue(MessageErrorCode.HEADLINE_EMPTY, MessageValidationSeverity.ERROR, "headline", "Headline is empty.", "Provide a conclusion-first headline.", related_slide_id=design.slide_blueprint_id))
    if design.headline.strip().lower() in NOUN_ONLY_HEADLINES:
        issues.append(_issue(MessageErrorCode.HEADLINE_NOUN_ONLY, MessageValidationSeverity.WARNING, "headline", "Headline appears to be a noun-only label.", "State the claim or decision implication.", related_slide_id=design.slide_blueprint_id))
    if not design.main_message.strip():
        issues.append(_issue(MessageErrorCode.MAIN_EMPTY, MessageValidationSeverity.ERROR, "main_message", "Main message is empty.", "Provide one clear main message.", related_slide_id=design.slide_blueprint_id))
    if design.headline.strip() == design.main_message.strip() or design.headline.strip() == design.key_takeaway.strip():
        issues.append(_issue(MessageErrorCode.MAIN_EMPTY, MessageValidationSeverity.WARNING, "main_message", "Headline, main message, or takeaway are duplicated.", "Give each field a distinct role.", related_slide_id=design.slide_blueprint_id))
    support_texts = [item.text.strip() for item in design.supporting_messages]
    if len(support_texts) != len(set(support_texts)):
        issues.append(_issue(MessageErrorCode.SUPPORT_DUPLICATE, MessageValidationSeverity.WARNING, "supporting_messages", "Supporting messages contain duplicates.", "Remove duplicate support points.", related_slide_id=design.slide_blueprint_id))
    if design.speaker_note_summary.strip() in {design.headline.strip(), design.main_message.strip()}:
        issues.append(_issue(MessageErrorCode.SPEAKER_NOTE_COPY, MessageValidationSeverity.WARNING, "speaker_note_summary", "Speaker note repeats visible message text.", "Use speaker note for presenter guidance, not copy repetition.", related_slide_id=design.slide_blueprint_id))


def _validate_language_safety(design: SlideMessageDesign, issues: list[MessageValidationIssue]) -> None:
    text = _all_text(design)
    placeholders = _contains_any(text, PLACEHOLDER_LABELS)
    if placeholders:
        issues.append(_issue(MessageErrorCode.PLACEHOLDER, MessageValidationSeverity.ERROR, "message", f"Placeholder text detected: {', '.join(placeholders[:4])}", "Remove placeholder or internal labels.", related_slide_id=design.slide_blueprint_id))
    internal = _contains_any(text, INTERNAL_LABEL_PATTERNS)
    if internal:
        issues.append(_issue(MessageErrorCode.INTERNAL_LABEL, MessageValidationSeverity.WARNING, "message", f"Internal label detected: {', '.join(internal[:4])}", "Avoid exposing implementation labels to customers.", related_slide_id=design.slide_blueprint_id))
    weak = _contains_any(text, WEAK_LANGUAGE)
    if weak:
        issues.append(_issue(MessageErrorCode.WEAK_LANGUAGE, MessageValidationSeverity.WARNING, "message", f"Weak language detected: {', '.join(weak[:4])}", "Pair abstract wording with specific target, change, or evidence.", related_slide_id=design.slide_blueprint_id))
    ambiguous = _contains_any(text, AMBIGUOUS_LANGUAGE)
    if ambiguous:
        issues.append(_issue(MessageErrorCode.AMBIGUOUS_LANGUAGE, MessageValidationSeverity.WARNING, "message", f"Ambiguous language detected: {', '.join(ambiguous[:4])}", "Clarify the target, condition, or timeframe.", related_slide_id=design.slide_blueprint_id))


def _validate_evidence(design: SlideMessageDesign, issues: list[MessageValidationIssue]) -> None:
    required = set(design.used_evidence_ids + design.unused_required_evidence_ids)
    used = set(design.used_evidence_ids)
    if design.evidence_alignment_level == EvidenceAlignmentLevel.EVIDENCE_MISSING.value and not design.missing_evidence_disclosure:
        issues.append(_issue(MessageErrorCode.EVIDENCE_MISSING, MessageValidationSeverity.ERROR, "missing_evidence_disclosure", "Evidence is missing but no disclosure is provided.", "Add a missing evidence disclosure.", related_slide_id=design.slide_blueprint_id))
    if design.evidence_alignment_level == EvidenceAlignmentLevel.EVIDENCE_SUPPORTED.value and design.unused_required_evidence_ids:
        issues.append(_issue(MessageErrorCode.EVIDENCE_ALIGNMENT, MessageValidationSeverity.WARNING, "unused_required_evidence_ids", "Evidence is marked supported but unused required evidence remains.", "Use all required evidence or lower alignment level.", related_slide_id=design.slide_blueprint_id, related_evidence_ids=design.unused_required_evidence_ids))
    if design.numeric_claims:
        for claim in design.numeric_claims:
            if not claim.basis_evidence_ids:
                issues.append(_issue(MessageErrorCode.NUMERIC_UNSUPPORTED, MessageValidationSeverity.ERROR, "numeric_claims", "Numeric claim has no evidence basis.", "Attach basis evidence IDs.", related_slide_id=design.slide_blueprint_id))
    elif _has_digits(_all_text(design)) and not used:
        issues.append(_issue(MessageErrorCode.NUMERIC_UNSUPPORTED, MessageValidationSeverity.WARNING, "message", "Message contains a numeric expression without used evidence.", "Avoid numeric claims unless evidence is available.", related_slide_id=design.slide_blueprint_id))
    if design.unsupported_claims:
        issues.append(_issue(MessageErrorCode.EVIDENCE_ALIGNMENT, MessageValidationSeverity.WARNING, "unsupported_claims", "Unsupported claims are present.", "Remove the claim or collect supporting evidence.", related_slide_id=design.slide_blueprint_id))
    if not required and design.evidence_alignment_level != EvidenceAlignmentLevel.NOT_APPLICABLE.value:
        issues.append(_issue(MessageErrorCode.EVIDENCE_ALIGNMENT, MessageValidationSeverity.INFO, "used_evidence_ids", "No evidence IDs are referenced.", "Confirm whether evidence is not applicable for this slide.", related_slide_id=design.slide_blueprint_id))


def validate_slide_message_design(payload: SlideMessageDesign | dict[str, Any], *, normalize: bool = False) -> MessageValidationResult:
    try:
        if isinstance(payload, SlideMessageDesign):
            design = payload
        else:
            data, _changed = normalize_slide_message_design_dict(payload) if normalize else (payload, [])
            design = SlideMessageDesign.parse_obj(data)
    except PydanticValidationError as exc:
        issues = _pydantic_issues(exc)
        return MessageValidationResult(valid=False, status=MessageStatus.INVALID, issues=issues)

    issues: list[MessageValidationIssue] = []
    if design.message_design_version != SUPPORTED_MESSAGE_DESIGN_VERSION or design.schema_version != SUPPORTED_MESSAGE_DESIGN_VERSION:
        issues.append(_issue(MessageErrorCode.VERSION_MISMATCH, MessageValidationSeverity.ERROR, "message_design_version", "Unsupported message design version.", f"Use {SUPPORTED_MESSAGE_DESIGN_VERSION}.", related_slide_id=design.slide_blueprint_id))
    _validate_lengths(design, issues)
    _validate_message_quality(design, issues)
    _validate_language_safety(design, issues)
    _validate_evidence(design, issues)
    errors = [item for item in issues if item.severity == MessageValidationSeverity.ERROR.value]
    return MessageValidationResult(
        valid=not errors,
        status=MessageStatus.INVALID if errors else MessageStatus.VALIDATED,
        issues=issues,
    )


def validate_message_designer_output(payload: MessageDesignerOutput | dict[str, Any], *, normalize: bool = False) -> MessageValidationResult:
    try:
        if isinstance(payload, MessageDesignerOutput):
            output = payload
        else:
            data, _changed = normalize_message_designer_output_dict(payload) if normalize else (payload, [])
            output = MessageDesignerOutput.parse_obj(data)
    except PydanticValidationError as exc:
        return MessageValidationResult(valid=False, status=MessageStatus.INVALID, issues=_pydantic_issues(exc))

    issues: list[MessageValidationIssue] = []
    if output.message_designer_output_version != SUPPORTED_MESSAGE_DESIGNER_OUTPUT_VERSION:
        issues.append(_issue(MessageErrorCode.VERSION_MISMATCH, MessageValidationSeverity.ERROR, "message_designer_output_version", "Unsupported message designer output version.", f"Use {SUPPORTED_MESSAGE_DESIGNER_OUTPUT_VERSION}."))
    duplicate_orders = _duplicates([str(item.slide_order) for item in output.slide_messages])
    if duplicate_orders:
        issues.append(_issue(MessageErrorCode.REFERENCE_MISSING, MessageValidationSeverity.ERROR, "slide_messages.slide_order", "Duplicate slide orders detected.", "Use one message per slide order."))
    duplicate_ids = _duplicates([item.slide_blueprint_id for item in output.slide_messages])
    if duplicate_ids:
        issues.append(_issue(MessageErrorCode.REFERENCE_MISSING, MessageValidationSeverity.ERROR, "slide_messages.slide_blueprint_id", "Duplicate slide references detected.", "Use one message per slide blueprint ID."))
    for item in output.slide_messages:
        result = validate_slide_message_design(item)
        issues.extend(result.issues)
    errors = [item for item in issues if item.severity == MessageValidationSeverity.ERROR.value]
    return MessageValidationResult(valid=not errors, status=MessageStatus.INVALID if errors else MessageStatus.VALIDATED, issues=issues)


def _duplicates(values: Iterable[str]) -> list[str]:
    seen = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates
