"""Deck-level semantic validators for Presentation Engine 2.0 Phase 1.5."""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from pydantic import ValidationError as PydanticValidationError

from .deck_contracts import (
    APPENDIX_ALLOWED_AFTER,
    AUDIENCE_RULES,
    DECK_LENGTH_LIMITS,
    DECK_PLACEHOLDER_LABELS,
    EXECUTIVE_REQUIRED_SECTIONS,
    REQUIRED_SECTION_TYPES,
    STORY_ARC_SECTION_RULES,
    TERMINAL_SECTION_TYPES,
)
from .deck_enums import (
    AudienceSeniority,
    DeckStatus,
    DeckValidationSeverity,
    NarrativeFunction,
    SectionType,
)
from .deck_errors import DeckErrorCode, SUPPORTED_DECK_BLUEPRINT_VERSION
from .deck_models import DeckBlueprint, DeckValidationIssue, DeckValidationResult
from .deck_normalizers import normalize_deck_blueprint_dict


def _issue(
    code: str,
    severity: DeckValidationSeverity,
    field_path: str,
    message: str,
    suggestion: str,
    *,
    blocking: bool | None = None,
    source: str = "deck_validator",
    related_slide_ids: Sequence[str] | None = None,
    related_section_ids: Sequence[str] | None = None,
) -> DeckValidationIssue:
    is_blocking = severity == DeckValidationSeverity.ERROR if blocking is None else blocking
    safe_message = message if len(message) <= 280 else f"{message[:260]}..."
    safe_suggestion = suggestion if len(suggestion) <= 280 else f"{suggestion[:260]}..."
    return DeckValidationIssue(
        code=code,
        severity=severity,
        field_path=field_path,
        message=safe_message,
        suggestion=safe_suggestion,
        blocking=is_blocking,
        source=source,
        related_slide_ids=list(related_slide_ids or []),
        related_section_ids=list(related_section_ids or []),
    )


def _pydantic_issues(error: PydanticValidationError) -> list[DeckValidationIssue]:
    issues: list[DeckValidationIssue] = []
    for item in error.errors():
        field_path = ".".join(str(part) for part in item.get("loc", ("payload",)))
        err_type = str(item.get("type", ""))
        code = DeckErrorCode.SCHEMA_REQUIRED
        if "enum" in err_type:
            code = DeckErrorCode.SCHEMA_ENUM
        elif "max_length" in err_type or "min_length" in err_type:
            code = DeckErrorCode.SCHEMA_LENGTH
        issues.append(
            _issue(
                code,
                DeckValidationSeverity.ERROR,
                field_path,
                str(item.get("msg", "Invalid deck field")),
                "Fix the field so it matches the Deck Blueprint schema.",
                source="schema",
            )
        )
    return issues


def _duplicates(values: Iterable[str]) -> list[str]:
    seen = set()
    duplicates = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates


def _contains_placeholder(value: str | None) -> bool:
    text = str(value or "").strip().lower()
    return text in DECK_PLACEHOLDER_LABELS


def _section_types(deck: DeckBlueprint) -> list[str]:
    return [section.section_type for section in sorted(deck.sections, key=lambda item: item.section_order)]


def _slide_orders(deck: DeckBlueprint) -> list[int]:
    return [slide.slide_order for slide in sorted(deck.slide_plan, key=lambda item: item.slide_order)]


def _validate_identity(deck: DeckBlueprint, issues: list[DeckValidationIssue]) -> None:
    if deck.deck_blueprint_version != SUPPORTED_DECK_BLUEPRINT_VERSION or deck.schema_version != SUPPORTED_DECK_BLUEPRINT_VERSION:
        issues.append(
            _issue(
                DeckErrorCode.SCHEMA_REQUIRED,
                DeckValidationSeverity.ERROR,
                "deck_blueprint_version",
                "Unsupported deck blueprint version.",
                f"Use {SUPPORTED_DECK_BLUEPRINT_VERSION}.",
            )
        )

    duplicate_sections = _duplicates([section.section_id for section in deck.sections])
    if duplicate_sections:
        issues.append(
            _issue(
                DeckErrorCode.SCHEMA_DUPLICATE_ID,
                DeckValidationSeverity.ERROR,
                "sections.section_id",
                f"Duplicate section IDs detected: {', '.join(duplicate_sections)}",
                "Use stable unique section IDs.",
                related_section_ids=duplicate_sections,
            )
        )

    slide_ids = [slide.slide_blueprint_id for slide in deck.slide_plan if slide.slide_blueprint_id]
    duplicate_slides = _duplicates(slide_ids)
    if duplicate_slides:
        issues.append(
            _issue(
                DeckErrorCode.SCHEMA_DUPLICATE_ID,
                DeckValidationSeverity.ERROR,
                "slide_plan.slide_blueprint_id",
                f"Duplicate slide blueprint IDs detected: {', '.join(duplicate_slides)}",
                "Use one slide blueprint ID per slide plan item.",
                related_slide_ids=duplicate_slides,
            )
        )

    duplicate_section_orders = _duplicates([str(section.section_order) for section in deck.sections])
    if duplicate_section_orders:
        issues.append(
            _issue(
                DeckErrorCode.STRUCTURE_ORDER,
                DeckValidationSeverity.ERROR,
                "sections.section_order",
                "Section order values must be unique.",
                "Assign a unique section_order to each section.",
            )
        )

    duplicate_slide_orders = _duplicates([str(order) for order in _slide_orders(deck)])
    if duplicate_slide_orders:
        issues.append(
            _issue(
                DeckErrorCode.STRUCTURE_ORDER,
                DeckValidationSeverity.ERROR,
                "slide_plan.slide_order",
                "Slide order values must be unique.",
                "Assign a unique slide_order to each slide plan item.",
            )
        )


def _validate_structure(deck: DeckBlueprint, issues: list[DeckValidationIssue]) -> None:
    ordered_sections = sorted(deck.sections, key=lambda item: item.section_order)
    ordered_section_types = [section.section_type for section in ordered_sections]
    ordered_slides = sorted(deck.slide_plan, key=lambda item: item.slide_order)
    section_ids = {section.section_id for section in deck.sections}
    planned_slide_ids = {slide.slide_blueprint_id for slide in deck.slide_plan if slide.slide_blueprint_id}

    if not ordered_section_types or ordered_section_types[0] != SectionType.COVER.value:
        issues.append(
            _issue(
                DeckErrorCode.STRUCTURE_MISSING,
                DeckValidationSeverity.ERROR,
                "sections[0].section_type",
                "The first section must be cover.",
                "Start the deck with a cover section.",
            )
        )

    if ordered_section_types and ordered_section_types[-1] not in TERMINAL_SECTION_TYPES:
        issues.append(
            _issue(
                DeckErrorCode.STRUCTURE_MISSING,
                DeckValidationSeverity.ERROR,
                "sections[-1].section_type",
                "The final section should be next_action, closing, or appendix.",
                "End with a decision-oriented section.",
            )
        )

    missing_required = REQUIRED_SECTION_TYPES - set(ordered_section_types)
    if missing_required:
        issues.append(
            _issue(
                DeckErrorCode.STRUCTURE_MISSING,
                DeckValidationSeverity.ERROR,
                "sections",
                f"Required sections are missing: {', '.join(sorted(missing_required))}",
                "Add the missing required sections.",
            )
        )

    if deck.audience_seniority == AudienceSeniority.EXECUTIVE.value:
        missing_executive = EXECUTIVE_REQUIRED_SECTIONS - set(ordered_section_types)
        if missing_executive:
            issues.append(
                _issue(
                    DeckErrorCode.AUDIENCE_FIT,
                    DeckValidationSeverity.ERROR,
                    "sections",
                    f"Executive decks require sections: {', '.join(sorted(missing_executive))}",
                    "Add an executive summary and clear decision path.",
                )
            )

    if SectionType.APPENDIX.value in ordered_section_types:
        appendix_index = ordered_section_types.index(SectionType.APPENDIX.value)
        previous = ordered_section_types[appendix_index - 1] if appendix_index > 0 else None
        if previous not in APPENDIX_ALLOWED_AFTER:
            issues.append(
                _issue(
                    DeckErrorCode.STRUCTURE_ORDER,
                    DeckValidationSeverity.WARNING,
                    "sections.appendix",
                    "Appendix should appear after next_action or closing.",
                    "Move appendix after the main decision flow.",
                )
            )

    for section in deck.sections:
        if section.section_id not in section_ids:
            continue
        if section.required and len(section.slide_ids) < section.minimum_slides:
            issues.append(
                _issue(
                    DeckErrorCode.STRUCTURE_COUNT,
                    DeckValidationSeverity.ERROR,
                    f"sections.{section.section_id}.slide_ids",
                    "Required section has fewer slides than minimum_slides.",
                    "Add slide references or lower the minimum only if intentional.",
                    related_section_ids=[section.section_id],
                )
            )
        if len(section.slide_ids) > section.maximum_slides:
            issues.append(
                _issue(
                    DeckErrorCode.STRUCTURE_COUNT,
                    DeckValidationSeverity.WARNING,
                    f"sections.{section.section_id}.slide_ids",
                    "Section has more slides than maximum_slides.",
                    "Split or move detail to appendix.",
                    related_section_ids=[section.section_id],
                )
            )
        for slide_id in section.slide_ids:
            if slide_id not in planned_slide_ids:
                issues.append(
                    _issue(
                        DeckErrorCode.STRUCTURE_REFERENCE,
                        DeckValidationSeverity.ERROR,
                        f"sections.{section.section_id}.slide_ids",
                        f"Section references missing slide blueprint ID: {slide_id}",
                        "Ensure every section slide_id exists in slide_plan or slide references.",
                        related_slide_ids=[slide_id],
                        related_section_ids=[section.section_id],
                    )
                )

    for slide in deck.slide_plan:
        if slide.section_id not in section_ids:
            issues.append(
                _issue(
                    DeckErrorCode.STRUCTURE_REFERENCE,
                    DeckValidationSeverity.ERROR,
                    f"slide_plan[{slide.slide_order}].section_id",
                    "Slide plan references a missing section.",
                    "Use a valid section_id.",
                    related_section_ids=[slide.section_id],
                )
            )

    min_count, max_count = DECK_LENGTH_LIMITS.get(deck.deck_length_type, (deck.minimum_slide_count, deck.maximum_slide_count))
    actual_count = len(deck.slide_plan)
    if actual_count < deck.minimum_slide_count or actual_count < min_count:
        issues.append(
            _issue(
                DeckErrorCode.STRUCTURE_COUNT,
                DeckValidationSeverity.ERROR,
                "slide_plan",
                "Deck has fewer slides than required by its length type.",
                "Add required story sections or adjust deck_length_type.",
            )
        )
    if actual_count > deck.maximum_slide_count or actual_count > max_count:
        issues.append(
            _issue(
                DeckErrorCode.STRUCTURE_COUNT,
                DeckValidationSeverity.WARNING,
                "slide_plan",
                "Deck has more slides than recommended by its length type.",
                "Move detail to appendix or select a longer deck type.",
            )
        )
    if deck.target_slide_count != actual_count:
        issues.append(
            _issue(
                DeckErrorCode.STRUCTURE_COUNT,
                DeckValidationSeverity.WARNING,
                "target_slide_count",
                "target_slide_count does not match the slide plan count.",
                "Keep target count aligned with the planned slide count.",
            )
        )

    if ordered_slides and ordered_slides[0].slide_role != "opening":
        issues.append(
            _issue(
                DeckErrorCode.STRUCTURE_ORDER,
                DeckValidationSeverity.WARNING,
                "slide_plan[0].slide_role",
                "The first slide should have an opening role.",
                "Use an opening cover slide.",
            )
        )


def _validate_story_arc(deck: DeckBlueprint, issues: list[DeckValidationIssue]) -> None:
    ordered_types = _section_types(deck)
    recommended = STORY_ARC_SECTION_RULES.get(deck.story_arc, [])
    if recommended:
        missing = [section_type for section_type in recommended if section_type in deck.required_sections and section_type not in ordered_types]
        if missing:
            issues.append(
                _issue(
                    DeckErrorCode.NARRATIVE_ORDER,
                    DeckValidationSeverity.ERROR,
                    "sections",
                    f"Story arc is missing required section types: {', '.join(missing)}",
                    "Add the missing sections for the selected story arc.",
                )
            )
        positions = {section_type: ordered_types.index(section_type) for section_type in ordered_types}
        for first, second in zip(recommended, recommended[1:]):
            if first in positions and second in positions and positions[first] > positions[second]:
                issues.append(
                    _issue(
                        DeckErrorCode.NARRATIVE_ORDER,
                        DeckValidationSeverity.ERROR,
                        "sections",
                        f"Story arc order is inconsistent: {first} appears after {second}.",
                        "Reorder sections to preserve narrative flow.",
                    )
                )

    solution_index = next((i for i, slide in enumerate(deck.slide_plan) if slide.narrative_function == "recommend"), None)
    problem_index = next((i for i, slide in enumerate(deck.slide_plan) if slide.narrative_function == "diagnose"), None)
    if problem_index is not None and solution_index is not None and solution_index < problem_index:
        issues.append(
            _issue(
                DeckErrorCode.NARRATIVE_ORDER,
                DeckValidationSeverity.ERROR,
                "slide_plan",
                "Recommendation appears before diagnosis.",
                "Explain the problem before presenting the recommendation.",
            )
        )

    if deck.story_beats:
        functions = [beat.narrative_function for beat in deck.story_beats]
        if NarrativeFunction.RECOMMEND.value in functions and NarrativeFunction.DIAGNOSE.value in functions:
            if functions.index(NarrativeFunction.RECOMMEND.value) < functions.index(NarrativeFunction.DIAGNOSE.value):
                issues.append(
                    _issue(
                        DeckErrorCode.NARRATIVE_COHERENCE,
                        DeckValidationSeverity.ERROR,
                        "story_beats",
                        "Story beats recommend before diagnosing.",
                        "Move diagnosis before recommendation.",
                    )
                )


def _validate_sales_quality(deck: DeckBlueprint, issues: list[DeckValidationIssue]) -> None:
    section_types = set(_section_types(deck))
    if SectionType.PRICING.value in section_types and not (
        SectionType.ROI.value in section_types or SectionType.KPI.value in section_types
    ):
        issues.append(
            _issue(
                DeckErrorCode.QUALITY_EVIDENCE,
                DeckValidationSeverity.WARNING,
                "sections",
                "Pricing appears without ROI or KPI support.",
                "Place value explanation before price discussion.",
            )
        )
    if SectionType.COMPETITOR.value in section_types and deck.key_differentiator == deck.value_proposition:
        issues.append(
            _issue(
                DeckErrorCode.QUALITY_EVIDENCE,
                DeckValidationSeverity.WARNING,
                "key_differentiator",
                "Competitive section exists but differentiator repeats value proposition.",
                "Clarify the specific winning difference.",
            )
        )
    if not deck.decision_points:
        issues.append(
            _issue(
                DeckErrorCode.QUALITY_CTA,
                DeckValidationSeverity.WARNING,
                "decision_points",
                "Deck has no decision points.",
                "Add the questions this deck should help answer.",
            )
        )
    if not deck.cta_plan.next_action or not deck.next_action:
        issues.append(
            _issue(
                DeckErrorCode.QUALITY_CTA,
                DeckValidationSeverity.ERROR,
                "cta_plan.next_action",
                "Deck requires a concrete next action.",
                "Define a next action that guides the decision process.",
            )
        )


def _validate_audience(deck: DeckBlueprint, issues: list[DeckValidationIssue]) -> None:
    rules = AUDIENCE_RULES.get(deck.audience_seniority)
    if not rules:
        return
    if rules.get("requires_executive_summary") and SectionType.EXECUTIVE_SUMMARY.value not in _section_types(deck):
        issues.append(
            _issue(
                DeckErrorCode.AUDIENCE_FIT,
                DeckValidationSeverity.ERROR,
                "sections",
                "This audience seniority requires an executive summary.",
                "Add an executive_summary section near the beginning.",
            )
        )
    if deck.target_slide_count > int(rules.get("detail_warning_threshold", 99)):
        issues.append(
            _issue(
                DeckErrorCode.AUDIENCE_FIT,
                DeckValidationSeverity.WARNING,
                "target_slide_count",
                "Deck may be too detailed for the audience seniority.",
                "Move details to appendix or reduce the main deck.",
            )
        )


def _validate_cleanliness(deck: DeckBlueprint, issues: list[DeckValidationIssue]) -> None:
    text_fields = {
        "deck_title": deck.deck_title,
        "core_thesis": deck.core_thesis,
        "value_proposition": deck.value_proposition,
        "key_differentiator": deck.key_differentiator,
        "opening_message": deck.opening_message,
        "problem_statement": deck.problem_statement,
        "insight_statement": deck.insight_statement,
        "recommendation_statement": deck.recommendation_statement,
        "impact_statement": deck.impact_statement,
        "closing_message": deck.closing_message,
        "next_action": deck.next_action,
    }
    for field_path, value in text_fields.items():
        if _contains_placeholder(value):
            issues.append(
                _issue(
                    DeckErrorCode.SAFETY_PLACEHOLDER,
                    DeckValidationSeverity.ERROR,
                    field_path,
                    "Deck contains an internal placeholder label.",
                    "Replace it with customer-facing Japanese wording.",
                )
            )

    for index, slide in enumerate(deck.slide_plan):
        if _contains_placeholder(slide.working_title) or _contains_placeholder(slide.key_message):
            issues.append(
                _issue(
                    DeckErrorCode.SAFETY_PLACEHOLDER,
                    DeckValidationSeverity.ERROR,
                    f"slide_plan[{index}]",
                    "Slide plan contains an internal placeholder label.",
                    "Replace it with natural proposal wording.",
                    related_slide_ids=[slide.slide_blueprint_id] if slide.slide_blueprint_id else [],
                )
            )


def _validate_slide_blueprint_refs(deck: DeckBlueprint, issues: list[DeckValidationIssue]) -> None:
    plan_by_id = {slide.slide_blueprint_id: slide for slide in deck.slide_plan if slide.slide_blueprint_id}
    refs_by_id = {ref.slide_blueprint_id: ref for ref in deck.slide_blueprint_refs}

    missing_refs = [slide_id for slide_id in plan_by_id if slide_id not in refs_by_id]
    if missing_refs:
        issues.append(
            _issue(
                DeckErrorCode.SAFETY_SLIDE_REFERENCE,
                DeckValidationSeverity.ERROR,
                "slide_blueprint_refs",
                "Slide plan items are missing Slide Blueprint references.",
                "Add slide_blueprint_refs for every required planned slide.",
                related_slide_ids=missing_refs[:10],
            )
        )

    for ref_id, ref in refs_by_id.items():
        plan = plan_by_id.get(ref_id)
        if not plan:
            issues.append(
                _issue(
                    DeckErrorCode.STRUCTURE_REFERENCE,
                    DeckValidationSeverity.WARNING,
                    "slide_blueprint_refs",
                    "Slide Blueprint reference has no matching slide plan item.",
                    "Remove unused references or add a slide plan item.",
                    related_slide_ids=[ref_id],
                )
            )
            continue
        if ref.expected_slide_type != plan.slide_type or ref.expected_slide_goal != plan.slide_goal:
            issues.append(
                _issue(
                    DeckErrorCode.SAFETY_SLIDE_REFERENCE,
                    DeckValidationSeverity.ERROR,
                    "slide_blueprint_refs",
                    "Slide Blueprint reference expected type or goal differs from slide plan.",
                    "Keep deck-level expectation and slide-level contract aligned.",
                    related_slide_ids=[ref_id],
                )
            )
        if ref.embedded_slide_blueprint:
            embedded = ref.embedded_slide_blueprint
            if embedded.slide_id != ref.slide_id:
                issues.append(
                    _issue(
                        DeckErrorCode.SAFETY_SLIDE_REFERENCE,
                        DeckValidationSeverity.ERROR,
                        "slide_blueprint_refs.embedded_slide_blueprint",
                        "Embedded Slide Blueprint slide_id does not match the deck reference.",
                        "Use a matching slide_id or remove the embedded blueprint.",
                        related_slide_ids=[ref_id],
                    )
                )


def validate_deck_blueprint(payload: DeckBlueprint | dict[str, Any], *, normalize: bool = False) -> DeckValidationResult:
    issues: list[DeckValidationIssue] = []
    try:
        data = payload
        if normalize and isinstance(payload, dict):
            data, _changed = normalize_deck_blueprint_dict(payload)
        deck = payload if isinstance(payload, DeckBlueprint) else DeckBlueprint.parse_obj(data)
    except PydanticValidationError as error:
        issues.extend(_pydantic_issues(error))
        return DeckValidationResult(valid=False, status=DeckStatus.INVALID, issues=issues)

    _validate_identity(deck, issues)
    _validate_structure(deck, issues)
    _validate_story_arc(deck, issues)
    _validate_sales_quality(deck, issues)
    _validate_audience(deck, issues)
    _validate_cleanliness(deck, issues)
    _validate_slide_blueprint_refs(deck, issues)

    has_errors = any(issue.severity == DeckValidationSeverity.ERROR.value for issue in issues)
    has_warnings = any(issue.severity == DeckValidationSeverity.WARNING.value for issue in issues)
    status = DeckStatus.INVALID if has_errors else DeckStatus.NEEDS_REVIEW if has_warnings else DeckStatus.READY_FOR_STORY_REVIEW
    return DeckValidationResult(valid=not has_errors, status=status, issues=issues)
