"""Cross-module validators for Alpha Integration Review."""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from ..deck_models import DeckBlueprint
from ..deck_planner.planner_models import ProposalContext
from ..deck_validators import validate_deck_blueprint
from ..evidence_planner.evidence_models import EvidencePlannerResult, MissingEvidenceSeverity
from ..message_designer.designer_models import MessageDesignerOutput
from ..message_designer.designer_validators import validate_message_designer_output
from .pipeline_models import (
    AlphaIssueCode,
    AlphaPipelineStage,
    AlphaValidationIssue,
    AlphaValidationSeverity,
    CrossModuleValidationResult,
)


def _issue(
    code: str,
    severity: AlphaValidationSeverity,
    stage: AlphaPipelineStage,
    field_path: str,
    case_id: str,
    message: str,
    reason: str,
    suggestion: str,
    *,
    blocking: bool | None = None,
    source_module: str = "alpha_integration",
    slide_id: str | None = None,
    evidence_id: str | None = None,
) -> AlphaValidationIssue:
    return AlphaValidationIssue(
        code=code,
        severity=severity,
        stage=stage,
        field_path=field_path,
        case_id=case_id,
        slide_id=slide_id,
        evidence_id=evidence_id,
        message=message,
        reason=reason,
        suggestion=suggestion,
        blocking=severity == AlphaValidationSeverity.ERROR if blocking is None else blocking,
        source_module=source_module,
    )


def _duplicates(values: Iterable[str]) -> list[str]:
    counter = Counter(values)
    return [value for value, count in counter.items() if count > 1]


def validate_evidence_stage(
    *,
    case_id: str,
    deck: DeckBlueprint,
    evidence: EvidencePlannerResult,
) -> CrossModuleValidationResult:
    issues: list[AlphaValidationIssue] = []
    deck_ids = [str(item.slide_blueprint_id) for item in deck.slide_plan if item.slide_blueprint_id]
    evidence_ids = [item.slide_blueprint_id for item in evidence.slide_evidence]
    deck_id_set = set(deck_ids)
    evidence_id_set = set(evidence_ids)

    if evidence.deck_id != deck.deck_id:
        issues.append(
            _issue(
                AlphaIssueCode.REFERENCE,
                AlphaValidationSeverity.ERROR,
                AlphaPipelineStage.EVIDENCE_VALIDATION,
                "evidence_planner_result.deck_id",
                case_id,
                "Evidence Planner deck_id does not match Deck Blueprint.",
                "Evidence output may belong to another deck.",
                "Regenerate evidence from the same Deck Blueprint.",
                source_module="evidence_planner",
            )
        )
    for slide_id in sorted(deck_id_set - evidence_id_set):
        issues.append(
            _issue(
                AlphaIssueCode.REFERENCE,
                AlphaValidationSeverity.ERROR,
                AlphaPipelineStage.EVIDENCE_VALIDATION,
                "slide_evidence",
                case_id,
                "Deck slide has no evidence plan.",
                "Every deck slide must have an evidence plan before message design.",
                "Create evidence requirements for the missing slide.",
                slide_id=slide_id,
                source_module="evidence_planner",
            )
        )
    for slide_id in sorted(evidence_id_set - deck_id_set):
        issues.append(
            _issue(
                AlphaIssueCode.REFERENCE,
                AlphaValidationSeverity.ERROR,
                AlphaPipelineStage.EVIDENCE_VALIDATION,
                "slide_evidence",
                case_id,
                "Evidence plan references a slide not present in the deck.",
                "Evidence output and Deck Blueprint are out of sync.",
                "Remove the orphan evidence plan or regenerate from the deck.",
                slide_id=slide_id,
                source_module="evidence_planner",
            )
        )
    for slide in evidence.slide_evidence:
        if not slide.required_evidence:
            issues.append(
                _issue(
                    AlphaIssueCode.EVIDENCE,
                    AlphaValidationSeverity.ERROR,
                    AlphaPipelineStage.EVIDENCE_VALIDATION,
                    "slide_evidence.required_evidence",
                    case_id,
                    "A slide has no required evidence.",
                    "Message Designer cannot verify claims without required evidence.",
                    "Add at least one required evidence item.",
                    slide_id=slide.slide_blueprint_id,
                    source_module="evidence_planner",
                )
            )
        if slide.numeric_evidence_required and not any(item.numeric_required for item in slide.required_evidence):
            issues.append(
                _issue(
                    AlphaIssueCode.EVIDENCE,
                    AlphaValidationSeverity.ERROR,
                    AlphaPipelineStage.EVIDENCE_VALIDATION,
                    "slide_evidence.numeric_evidence_required",
                    case_id,
                    "Numeric evidence flag is true but no numeric requirement exists.",
                    "Numeric integrity cannot be checked downstream.",
                    "Mark at least one required evidence item as numeric_required.",
                    slide_id=slide.slide_blueprint_id,
                    source_module="evidence_planner",
                )
            )
        if any(warning.severity == MissingEvidenceSeverity.BLOCKING.value for warning in slide.missing_evidence_warnings):
            issues.append(
                _issue(
                    AlphaIssueCode.EVIDENCE,
                    AlphaValidationSeverity.WARNING,
                    AlphaPipelineStage.EVIDENCE_VALIDATION,
                    "slide_evidence.missing_evidence_warnings",
                    case_id,
                    "Blocking missing evidence exists for this slide.",
                    "The pipeline can continue for review, but Phase 2D should preserve the disclosure.",
                    "Collect missing evidence before customer-facing rendering.",
                    slide_id=slide.slide_blueprint_id,
                    source_module="evidence_planner",
                    blocking=False,
                )
            )
    return _result(issues)


def validate_cross_module(
    *,
    case_id: str,
    context: ProposalContext,
    deck: DeckBlueprint,
    evidence: EvidencePlannerResult,
    message: MessageDesignerOutput,
) -> CrossModuleValidationResult:
    issues: list[AlphaValidationIssue] = []
    deck_validation = validate_deck_blueprint(deck)
    message_validation = validate_message_designer_output(message)
    for item in deck_validation.issues:
        severity = AlphaValidationSeverity.ERROR if item.severity == "error" else AlphaValidationSeverity.WARNING
        issues.append(
            _issue(
                AlphaIssueCode.DECK,
                severity,
                AlphaPipelineStage.DECK_VALIDATION,
                item.field_path,
                case_id,
                item.message,
                "Deck Blueprint validation reported an issue.",
                item.suggestion or "Review Deck Blueprint contract.",
                source_module="deck_planner",
                blocking=item.blocking,
            )
        )
    for item in message_validation.issues:
        severity = AlphaValidationSeverity.ERROR if item.severity == "error" else AlphaValidationSeverity.WARNING
        issues.append(
            _issue(
                AlphaIssueCode.MESSAGE,
                severity,
                AlphaPipelineStage.MESSAGE_VALIDATION,
                item.field_path,
                case_id,
                item.message,
                "Message Designer validation reported an issue.",
                item.suggestion or "Review Message Designer output.",
                source_module="message_designer",
                slide_id=item.related_slide_id,
                blocking=item.blocking,
            )
        )

    deck_slide_ids = [str(item.slide_blueprint_id) for item in deck.slide_plan if item.slide_blueprint_id]
    evidence_slide_ids = [item.slide_blueprint_id for item in evidence.slide_evidence]
    message_slide_ids = [item.slide_blueprint_id for item in message.slide_messages]
    all_id_sets = [set(deck_slide_ids), set(evidence_slide_ids), set(message_slide_ids)]
    if not (all_id_sets[0] == all_id_sets[1] == all_id_sets[2]):
        issues.append(
            _issue(
                AlphaIssueCode.REFERENCE,
                AlphaValidationSeverity.ERROR,
                AlphaPipelineStage.CROSS_MODULE_VALIDATION,
                "slide_blueprint_id",
                case_id,
                "Slide references are not aligned across Deck, Evidence, and Message outputs.",
                "At least one module lost or added a slide reference.",
                "Regenerate all modules from the same Proposal Context.",
                source_module="alpha_integration",
            )
        )
    for duplicate in _duplicates(deck_slide_ids + evidence_slide_ids + message_slide_ids):
        if duplicate in deck_slide_ids and duplicate in evidence_slide_ids and duplicate in message_slide_ids:
            continue
        issues.append(
            _issue(
                AlphaIssueCode.REFERENCE,
                AlphaValidationSeverity.ERROR,
                AlphaPipelineStage.CROSS_MODULE_VALIDATION,
                "slide_blueprint_id",
                case_id,
                "Duplicate or inconsistent slide ID detected.",
                "Reference stability is required for Phase 2D handoff.",
                "Ensure each slide has exactly one corresponding evidence and message record.",
                slide_id=duplicate,
                source_module="alpha_integration",
            )
        )

    deck_orders = [item.slide_order for item in deck.slide_plan]
    message_orders = [item.slide_order for item in message.slide_messages]
    if deck_orders != message_orders:
        issues.append(
            _issue(
                AlphaIssueCode.REFERENCE,
                AlphaValidationSeverity.ERROR,
                AlphaPipelineStage.CROSS_MODULE_VALIDATION,
                "slide_order",
                case_id,
                "Slide order changed between Deck Planner and Message Designer.",
                "Phase 2D requires stable order.",
                "Keep Message Designer order identical to Deck Blueprint order.",
                source_module="alpha_integration",
            )
        )

    evidence_by_slide = {slide.slide_blueprint_id: slide for slide in evidence.slide_evidence}
    for msg in message.slide_messages:
        ev = evidence_by_slide.get(msg.slide_blueprint_id)
        if ev is None:
            continue
        evidence_ids = {item.requirement_id for item in [*ev.required_evidence, *ev.optional_evidence]}
        for used_id in msg.used_evidence_ids:
            if used_id not in evidence_ids:
                issues.append(
                    _issue(
                        AlphaIssueCode.REFERENCE,
                        AlphaValidationSeverity.ERROR,
                        AlphaPipelineStage.CROSS_MODULE_VALIDATION,
                        "message_designer_result.used_evidence_ids",
                        case_id,
                        "Message uses an evidence ID not produced by Evidence Planner.",
                        "Evidence traceability is broken.",
                        "Use only Evidence Planner requirement IDs.",
                        slide_id=msg.slide_blueprint_id,
                        evidence_id=used_id,
                        source_module="message_designer",
                    )
                )
        missing_blocking = any(w.severity == MissingEvidenceSeverity.BLOCKING.value for w in ev.missing_evidence_warnings)
        if missing_blocking and not msg.missing_evidence_disclosure:
            issues.append(
                _issue(
                    AlphaIssueCode.EVIDENCE,
                    AlphaValidationSeverity.ERROR,
                    AlphaPipelineStage.CROSS_MODULE_VALIDATION,
                    "message_designer_result.missing_evidence_disclosure",
                    case_id,
                    "Blocking missing evidence was not disclosed in the message output.",
                    "Message Designer must not hide evidence gaps.",
                    "Add missing evidence disclosure before Phase 2D.",
                    slide_id=msg.slide_blueprint_id,
                    source_module="message_designer",
                )
            )
        if msg.numeric_claims and not all(claim.basis_evidence_ids for claim in msg.numeric_claims):
            issues.append(
                _issue(
                    AlphaIssueCode.SAFETY,
                    AlphaValidationSeverity.ERROR,
                    AlphaPipelineStage.CROSS_MODULE_VALIDATION,
                    "message_designer_result.numeric_claims",
                    case_id,
                    "Numeric claim lacks basis evidence.",
                    "Unsupported numeric claims cannot proceed to Phase 2D.",
                    "Attach basis evidence IDs or remove the numeric claim.",
                    slide_id=msg.slide_blueprint_id,
                    source_module="message_designer",
                )
            )
        if msg.evidence_alignment_level == "evidence_missing" and msg.message_confidence == "high":
            issues.append(
                _issue(
                    AlphaIssueCode.EVIDENCE,
                    AlphaValidationSeverity.WARNING,
                    AlphaPipelineStage.CROSS_MODULE_VALIDATION,
                    "message_confidence",
                    case_id,
                    "Message confidence is too high for missing evidence.",
                    "Evidence gaps should reduce confidence.",
                    "Lower confidence or collect evidence.",
                    slide_id=msg.slide_blueprint_id,
                    source_module="message_designer",
                    blocking=False,
                )
            )

    if context.persona and str(deck.audience_profile.primary_audience if deck.audience_profile else deck.primary_audience) == "general":
        issues.append(
            _issue(
                AlphaIssueCode.AUDIENCE,
                AlphaValidationSeverity.WARNING,
                AlphaPipelineStage.CROSS_MODULE_VALIDATION,
                "deck_blueprint.primary_audience",
                case_id,
                "Context has persona but deck audience remains general.",
                "Audience inference may be too broad.",
                "Review audience mapping before Phase 2D.",
                source_module="deck_planner",
                blocking=False,
            )
        )

    if message.generated_pptx or message.generated_slide_blueprints or message.connected_to_runtime:
        issues.append(
            _issue(
                AlphaIssueCode.SAFETY,
                AlphaValidationSeverity.ERROR,
                AlphaPipelineStage.CROSS_MODULE_VALIDATION,
                "message_designer_result",
                case_id,
                "Message Designer crossed the offline boundary.",
                "Alpha Integration must remain offline and non-rendering.",
                "Remove runtime, PPTX, or Slide Blueprint generation.",
                source_module="message_designer",
            )
        )
    return _result(issues)


def _result(issues: list[AlphaValidationIssue]) -> CrossModuleValidationResult:
    error_count = len([item for item in issues if item.severity == AlphaValidationSeverity.ERROR.value])
    stage_names = {item.stage for item in issues}
    failed = len({item.stage for item in issues if item.severity == AlphaValidationSeverity.ERROR.value})
    checked = max(4, len(stage_names))
    return CrossModuleValidationResult(
        valid=error_count == 0,
        issues=issues,
        checked_stage_count=checked,
        passed_stage_count=max(0, checked - failed),
        failed_stage_count=failed,
    )
