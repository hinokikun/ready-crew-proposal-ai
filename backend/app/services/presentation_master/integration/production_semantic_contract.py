from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import re
from typing import Any


class SemanticAuthority(str, Enum):
    USER_EXPLICIT = "USER_EXPLICIT"
    SYSTEM_EXTRACTED = "SYSTEM_EXTRACTED"
    AI_PROPOSED = "AI_PROPOSED"
    EXISTING_STRUCTURED_AI_OUTPUT = "EXISTING_STRUCTURED_AI_OUTPUT"
    EXTERNAL_VERIFIED = "EXTERNAL_VERIFIED"
    UNRESOLVED = "UNRESOLVED"


class SemanticReviewState(str, Enum):
    UNCONFIRMED = "UNCONFIRMED"
    CONFIRMED = "CONFIRMED"
    CORRECTED = "CORRECTED"
    REJECTED = "REJECTED"
    UNRESOLVED = "UNRESOLVED"


class SemanticItemType(str, Enum):
    PREPARATION_ANALYSIS = "preparation_analysis"
    DECISION_CONDITION = "decision_condition"
    ACCOUNTABLE_OWNER = "accountable_owner"
    APPROVER = "approver"
    EXECUTION_ACTION = "execution_action"
    DECISION_CONTEXT = "decision_context"
    EVIDENCE = "evidence"
    KPI_NAME = "kpi_name"
    KPI_VALUE = "kpi_value"
    KPI_THRESHOLD = "kpi_threshold"
    ORDERED_STAGE = "ordered_stage"
    STAGE_OUTPUT = "stage_output"
    EXIT_CRITERION = "exit_criterion"
    ESCALATION = "escalation"


@dataclass(frozen=True)
class ProductionSemanticCandidate:
    id: str
    semantic_type: SemanticItemType
    value: str
    source_type: str
    source_field: str
    authority: SemanticAuthority
    confidence: float
    review_state: SemanticReviewState
    inferred: bool = False
    admissible_as_evidence: bool = False
    source_reference: str = ""
    from_item: str = ""
    to_item: str = ""
    relationship_type: str = ""
    original_candidate_id: str = ""
    confirmation_authority: SemanticAuthority | None = None

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.value.strip():
            raise ValueError("candidate id and value are required")
        if not 0 <= float(self.confidence) <= 1:
            raise ValueError("candidate confidence must be between 0 and 1")
        if self.review_state == SemanticReviewState.CONFIRMED and self.authority == SemanticAuthority.AI_PROPOSED and self.confirmation_authority is None:
            raise ValueError("confirmed AI candidates require confirmation authority metadata")

    @property
    def admissible_for_supply(self) -> bool:
        return self.review_state in {SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED} and self.authority in {SemanticAuthority.USER_EXPLICIT, SemanticAuthority.SYSTEM_EXTRACTED, SemanticAuthority.EXTERNAL_VERIFIED}


@dataclass(frozen=True)
class ProductionSemanticCandidateSet:
    candidates: tuple[ProductionSemanticCandidate, ...] = ()

    def __post_init__(self) -> None:
        if len({candidate.id for candidate in self.candidates}) != len(self.candidates):
            raise ValueError("candidate ids must be unique")

    def admissible(self) -> tuple[ProductionSemanticCandidate, ...]:
        return tuple(candidate for candidate in self.candidates if candidate.admissible_for_supply)

    def unresolved_critical(self) -> tuple[str, ...]:
        return tuple(candidate.id for candidate in self.candidates if candidate.review_state in {SemanticReviewState.UNCONFIRMED, SemanticReviewState.UNRESOLVED} or candidate.review_state == SemanticReviewState.REJECTED)


def confirm_candidate(candidate: ProductionSemanticCandidate, *, confirmation_authority: SemanticAuthority = SemanticAuthority.USER_EXPLICIT) -> ProductionSemanticCandidate:
    if candidate.review_state == SemanticReviewState.REJECTED:
        raise ValueError("rejected candidate cannot be confirmed")
    if confirmation_authority != SemanticAuthority.USER_EXPLICIT:
        raise ValueError("candidate confirmation requires USER_EXPLICIT authority")
    effective_authority = confirmation_authority if candidate.authority == SemanticAuthority.AI_PROPOSED else candidate.authority
    return replace(candidate, authority=effective_authority, review_state=SemanticReviewState.CONFIRMED, confirmation_authority=confirmation_authority)


def correct_candidate(candidate: ProductionSemanticCandidate, value: str) -> ProductionSemanticCandidate:
    if not value.strip():
        raise ValueError("corrected value is required")
    effective_authority = SemanticAuthority.USER_EXPLICIT if candidate.authority == SemanticAuthority.AI_PROPOSED else candidate.authority
    return replace(candidate, value=value.strip(), authority=effective_authority, review_state=SemanticReviewState.CORRECTED, inferred=False, confirmation_authority=SemanticAuthority.USER_EXPLICIT, original_candidate_id=candidate.original_candidate_id or candidate.id)


def reject_candidate(candidate: ProductionSemanticCandidate) -> ProductionSemanticCandidate:
    return replace(candidate, review_state=SemanticReviewState.REJECTED)


def candidate_set_to_dict(candidate_set: ProductionSemanticCandidateSet) -> dict[str, object]:
    return {"candidates": [{"id": item.id, "semantic_type": item.semantic_type.value, "value": item.value, "source_type": item.source_type, "source_field": item.source_field, "authority": item.authority.value, "confidence": item.confidence, "review_state": item.review_state.value, "inferred": item.inferred, "admissible_as_evidence": item.admissible_as_evidence, "source_reference": item.source_reference, "from_item": item.from_item, "to_item": item.to_item, "relationship_type": item.relationship_type, "original_candidate_id": item.original_candidate_id, "confirmation_authority": item.confirmation_authority.value if item.confirmation_authority else None} for item in candidate_set.candidates]}


def extract_explicit_candidates(payload: Any) -> ProductionSemanticCandidateSet:
    """Extract only explicitly labelled values from existing Production text."""
    text_sources = (("project_brief", getattr(payload, "project_brief", "")), ("hearing_result", getattr(payload, "hearing_result", "")))
    patterns = {
        SemanticItemType.DECISION_CONDITION: ("判断条件", "決定条件"),
        SemanticItemType.ACCOUNTABLE_OWNER: ("責任者",),
        SemanticItemType.APPROVER: ("承認者", "決裁者"),
        SemanticItemType.EXECUTION_ACTION: ("実施内容", "実行内容"),
        SemanticItemType.EVIDENCE: ("証拠", "根拠"),
    }
    candidates: list[ProductionSemanticCandidate] = []
    for source_field, source_text in text_sources:
        for semantic_type, labels in patterns.items():
            label_pattern = "|".join(re.escape(label) for label in labels)
            match = re.search(rf"(?:{label_pattern})\s*[:：]\s*([^\n]+)", str(source_text or ""))
            if not match:
                continue
            value = match.group(1).strip()
            candidate_id = f"explicit:{semantic_type.value}:{source_field}"
            candidates.append(ProductionSemanticCandidate(candidate_id, semantic_type, value, "user_text", source_field, SemanticAuthority.SYSTEM_EXTRACTED, 1.0, SemanticReviewState.CONFIRMED, source_reference=f"{source_field}:label", admissible_as_evidence=semantic_type == SemanticItemType.EVIDENCE))
    return ProductionSemanticCandidateSet(tuple(candidates))


def propose_candidates_from_analysis(analysis: Any) -> ProductionSemanticCandidateSet:
    """Expose analysis suggestions as review-required AI proposals."""
    if analysis is None:
        return ProductionSemanticCandidateSet()
    values = (
        (SemanticItemType.DECISION_CONDITION, getattr(getattr(analysis, "quality_check", None), "human_review_notes", ""), "analysis.quality_check.human_review_notes"),
        (SemanticItemType.EXECUTION_ACTION, getattr(analysis, "proposal_policy", ""), "analysis.proposal_policy"),
    )
    candidates = tuple(ProductionSemanticCandidate(f"ai:{item_type.value}", item_type, str(value).strip(), "analysis", source_field, SemanticAuthority.AI_PROPOSED, 0.6, SemanticReviewState.UNCONFIRMED, inferred=True) for item_type, value, source_field in values if str(value or "").strip())
    return ProductionSemanticCandidateSet(candidates)


__all__ = ["ProductionSemanticCandidate", "ProductionSemanticCandidateSet", "SemanticAuthority", "SemanticItemType", "SemanticReviewState", "candidate_set_to_dict", "confirm_candidate", "correct_candidate", "reject_candidate", "extract_explicit_candidates", "propose_candidates_from_analysis"]
