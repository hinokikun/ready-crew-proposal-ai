"""Offline validation and handoff for explicit proposal semantic sources."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from numbers import Number
from typing import Any

from .definitions import ALLOWED_PROVENANCE_STATES, SUPPORTED_RELATIONSHIP_TYPES
from .semantic_resolution import ResolutionSourceType
from .semantic_supplement import (
    DecisionCondition,
    EvidenceState,
    ProposalSemanticSupplement,
    ProposalStage,
    ResponsibilityAssignment,
    SupplementEvidenceBinding,
    SupplementMetric,
)


class SourceOrigin(str, Enum):
    STRATEGY_OUTPUT = "STRATEGY_OUTPUT"
    PROPOSAL_INTAKE = "PROPOSAL_INTAKE"
    HUMAN_INPUT = "HUMAN_INPUT"
    SOURCE_DOCUMENT = "SOURCE_DOCUMENT"
    EVIDENCE_REFERENCE = "EVIDENCE_REFERENCE"
    APPROVED_FIXTURE = "APPROVED_FIXTURE"
    DETERMINISTIC_DERIVATION = "DETERMINISTIC_DERIVATION"


class EvidenceGranularity(str, Enum):
    DOCUMENT_LEVEL = "DOCUMENT_LEVEL"
    SECTION_LEVEL = "SECTION_LEVEL"
    ITEM_LEVEL = "ITEM_LEVEL"


class BindingState(str, Enum):
    VALID = "VALID"
    PARTIAL = "PARTIAL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INVALID = "INVALID"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class SourceIdentity:
    identity_type: str
    identifier: str
    locator: str | None = None

    def __post_init__(self) -> None:
        if not self.identity_type.strip() or not self.identifier.strip():
            raise ValueError("source identity requires a type and identifier")


@dataclass(frozen=True)
class SourceDocumentReference:
    document_id: str
    source_label: str
    granularity: EvidenceGranularity
    page_or_section: str | None = None
    fragment_reference: str | None = None
    verification_state: str = "unverified"

    def __post_init__(self) -> None:
        if not self.document_id.strip() or not self.source_label.strip():
            raise ValueError("document reference requires identity and label")


@dataclass(frozen=True)
class SourceBindingInput:
    source_binding_id: str
    origin: SourceOrigin
    source_identity: SourceIdentity
    semantic_target: str
    semantic_role: str
    raw_value: Any = None
    structured_value: Any = None
    source_reference: SourceDocumentReference | str | None = None
    provenance_state: str = "supplied"
    evidence_state: EvidenceState = EvidenceState.NONE
    confidence: float = 0.0
    human_supplied: bool = False
    review_required: bool = False
    version: str | None = None

    def __post_init__(self) -> None:
        if not self.source_binding_id.strip() or not self.semantic_target.strip() or not self.semantic_role.strip():
            raise ValueError("source binding requires identity and semantic target")
        if self.provenance_state not in ALLOWED_PROVENANCE_STATES:
            raise ValueError(f"unsupported provenance state: {self.provenance_state}")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.human_supplied and self.origin != SourceOrigin.HUMAN_INPUT:
            raise ValueError("human_supplied bindings must use HUMAN_INPUT origin")
        if self.origin == SourceOrigin.HUMAN_INPUT and self.provenance_state in {"source_backed", "evidence_backed"}:
            raise ValueError("human input cannot silently become source-backed")


@dataclass(frozen=True)
class BindingValidationResult:
    binding_id: str
    source_identity: SourceIdentity
    semantic_target: str
    state: BindingState
    resolution_source_type: ResolutionSourceType | None
    provenance_state: str
    evidence_state: EvidenceState
    unresolved_issues: tuple[str, ...]
    reason: str
    human_review_required: bool


@dataclass(frozen=True)
class BindingSetResult:
    validations: tuple[BindingValidationResult, ...]
    conflicts: tuple[str, ...]
    supplement: ProposalSemanticSupplement | None
    state: BindingState


ORIGIN_TO_RESOLUTION_SOURCE = {
    SourceOrigin.STRATEGY_OUTPUT: ResolutionSourceType.STRATEGY_STRUCTURED,
    SourceOrigin.PROPOSAL_INTAKE: ResolutionSourceType.PROPOSAL_STRUCTURED,
    SourceOrigin.HUMAN_INPUT: ResolutionSourceType.HUMAN_SUPPLIED,
    SourceOrigin.SOURCE_DOCUMENT: ResolutionSourceType.SOURCE_REFERENCE,
    SourceOrigin.EVIDENCE_REFERENCE: ResolutionSourceType.ITEM_BOUND_EVIDENCE,
    SourceOrigin.APPROVED_FIXTURE: ResolutionSourceType.APPROVED_FIXTURE,
    SourceOrigin.DETERMINISTIC_DERIVATION: ResolutionSourceType.DERIVED_DETERMINISTIC,
}


def _value(binding: SourceBindingInput) -> Any:
    return binding.structured_value if binding.structured_value is not None else binding.raw_value


def _document_granularity(binding: SourceBindingInput) -> EvidenceGranularity | None:
    return binding.source_reference.granularity if isinstance(binding.source_reference, SourceDocumentReference) else None


def _validate_value(binding: SourceBindingInput) -> list[str]:
    value = _value(binding)
    issues: list[str] = []
    role = binding.semantic_role
    if role in {"kpi_current", "kpi_value", "kpi_target", "kpi_threshold"} and not isinstance(value, Number):
        issues.append("numeric KPI semantic requires a numeric-compatible value")
    if role == "stage_order" and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
        issues.append("stage order requires a non-negative integer")
    if role in {"accountable_owner", "responsible_executor", "approver", "decision_maker", "escalation_owner", "stakeholder", "consulted_party"} and not isinstance(value, str):
        issues.append("responsibility requires a party string")
    if role == "relationship":
        if not isinstance(value, dict) or not value.get("source") or not value.get("target") or value.get("type") not in SUPPORTED_RELATIONSHIP_TYPES:
            issues.append("relationship requires source, target, and supported type")
    if role == "decision_condition":
        if not isinstance(value, dict) or not value.get("outcome"):
            issues.append("decision condition requires an outcome")
    if role == "evidence" and not binding.semantic_target.strip():
        issues.append("evidence binding requires a semantic item target")
    return issues


def validate_source_binding(binding: SourceBindingInput, *, required_granularity: EvidenceGranularity | None = None) -> BindingValidationResult:
    source_type = ORIGIN_TO_RESOLUTION_SOURCE[binding.origin]
    issues = _validate_value(binding)
    granularity = _document_granularity(binding)
    if required_granularity == EvidenceGranularity.ITEM_LEVEL and granularity != EvidenceGranularity.ITEM_LEVEL:
        issues.append("document granularity does not satisfy item-level evidence requirement")
    if binding.origin == SourceOrigin.EVIDENCE_REFERENCE and binding.evidence_state != EvidenceState.ITEM_BOUND:
        issues.append("evidence reference must explicitly declare item-bound evidence")
    if binding.origin in {SourceOrigin.SOURCE_DOCUMENT, SourceOrigin.EVIDENCE_REFERENCE} and not binding.source_reference:
        issues.append("document/evidence origin requires an explicit source reference")
    if issues:
        state = BindingState.INVALID if any("requires" in issue or "numeric" in issue or "integer" in issue or "supported" in issue for issue in issues) else BindingState.PARTIAL
    elif binding.review_required:
        state = BindingState.REVIEW_REQUIRED
    else:
        state = BindingState.VALID
    return BindingValidationResult(binding.source_binding_id, binding.source_identity, binding.semantic_target, state, source_type, binding.provenance_state, binding.evidence_state, tuple(issues), "explicit source binding validated" if not issues else "source binding requires correction", binding.review_required or bool(issues))


def validate_source_bindings(bindings: tuple[SourceBindingInput, ...], *, required_granularity: EvidenceGranularity | None = None) -> BindingSetResult:
    validations = tuple(validate_source_binding(binding, required_granularity=required_granularity) for binding in bindings)
    conflicts: list[str] = []
    by_target: dict[tuple[str, str], list[SourceBindingInput]] = {}
    for binding in bindings:
        by_target.setdefault((binding.semantic_target, binding.semantic_role), []).append(binding)
    for (target, role), candidates in by_target.items():
        values = {repr(_value(binding)) for binding in candidates}
        if len(values) > 1:
            conflicts.append(f"conflict:{target}:{role}")
    if conflicts:
        state = BindingState.CONFLICT
    elif any(item.state == BindingState.INVALID for item in validations):
        state = BindingState.INVALID
    elif any(item.state in {BindingState.PARTIAL, BindingState.REVIEW_REQUIRED} for item in validations):
        state = BindingState.PARTIAL
    else:
        state = BindingState.VALID
    return BindingSetResult(validations, tuple(conflicts), bindings_to_supplement(bindings) if state not in {BindingState.INVALID, BindingState.CONFLICT} else None, state)


def bindings_to_supplement(bindings: tuple[SourceBindingInput, ...]) -> ProposalSemanticSupplement:
    """Convert validated explicit inputs to the existing supplement contract."""

    metrics: dict[str, dict[str, Any]] = {}
    stages: dict[str, dict[str, Any]] = {}
    responsibilities: list[ResponsibilityAssignment] = []
    conditions: list[DecisionCondition] = []
    relationships = []
    evidence: list[SupplementEvidenceBinding] = []
    for binding in bindings:
        value = _value(binding)
        source = binding.source_identity.identifier
        if binding.semantic_role in {"kpi_current", "kpi_value", "kpi_target", "kpi_threshold"}:
            metric = metrics.setdefault(binding.semantic_target, {"metric_id": binding.semantic_target, "name": binding.semantic_target, "source_binding": source, "provenance_state": binding.provenance_state, "human_supplied": binding.human_supplied, "confidence": binding.confidence})
            if source not in metric["source_binding"].split("|"):
                metric["source_binding"] = f"{metric['source_binding']}|{source}"
            field = {"kpi_current": "current_value", "kpi_value": "current_value", "kpi_target": "target_value", "kpi_threshold": "threshold"}[binding.semantic_role]
            metric[field] = value
        elif binding.semantic_role == "stage":
            data = value if isinstance(value, dict) else {"name": str(value)}
            stages[binding.semantic_target] = {"stage_id": binding.semantic_target, "name": data.get("name", binding.semantic_target), "semantic_purpose": data.get("purpose", "explicit process stage"), "order": data.get("order", 0), "outputs": tuple(data.get("outputs", ())), "exit_criterion_id": data.get("exit_criterion_id"), "source_binding": source, "provenance_state": binding.provenance_state, "confidence": binding.confidence}
        elif binding.semantic_role in {"accountable_owner", "responsible_executor", "approver", "decision_maker", "escalation_owner", "stakeholder", "consulted_party"}:
            responsibilities.append(ResponsibilityAssignment(binding.source_binding_id, str(value), binding.semantic_role, binding.semantic_target, binding.provenance_state, source, binding.human_supplied, binding.review_required, binding.confidence))
        elif binding.semantic_role == "decision_condition":
            data = value
            conditions.append(DecisionCondition(binding.semantic_target, data.get("meaning", binding.semantic_target), data.get("metric_id"), data.get("operator"), data.get("value"), data["outcome"], binding.provenance_state, source, binding.human_supplied, binding.review_required, binding.confidence))
        elif binding.semantic_role == "relationship":
            from .upstream_adapter import SemanticRelationship
            relationships.append(SemanticRelationship(value["type"], value["source"], value["target"], binding.confidence, binding.provenance_state, "DIRECT", "explicit source binding", binding.review_required))
        elif binding.semantic_role == "evidence":
            reference = binding.source_reference.document_id if isinstance(binding.source_reference, SourceDocumentReference) else str(binding.source_reference or source)
            evidence.append(SupplementEvidenceBinding(binding.source_binding_id, binding.semantic_target, binding.evidence_state, reference, binding.provenance_state, binding.review_required, binding.human_supplied))
    metric_values = tuple(SupplementMetric(**data) for data in metrics.values())
    stage_values = tuple(ProposalStage(**data) for data in stages.values())
    return ProposalSemanticSupplement(metrics=metric_values, stages=stage_values, responsibilities=tuple(responsibilities), decision_conditions=tuple(conditions), relationships=tuple(relationships), evidence_bindings=tuple(evidence), confidence=min((binding.confidence for binding in bindings), default=0.0))


__all__ = ["BindingSetResult", "BindingState", "BindingValidationResult", "EvidenceGranularity", "ORIGIN_TO_RESOLUTION_SOURCE", "SourceBindingInput", "SourceDocumentReference", "SourceIdentity", "SourceOrigin", "bindings_to_supplement", "validate_source_binding", "validate_source_bindings"]
