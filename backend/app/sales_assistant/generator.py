import json
from typing import Any, Dict, List, Tuple

from app.strategy_engine.term_guard import find_prohibited_terms

from .enums import ActionOwner, ActionPriority, MeetingStage, ObjectionType, QuestionPriority, ReviewSeverity
from .models import (
    DecisionMakerSupport,
    DiscoveryQuestion,
    EvidenceGuidance,
    FollowUp,
    GenerationMetadata,
    MeetingPlan,
    NextAction,
    ObjectionHandlingItem,
    RiskAndGuardrails,
    SalesAssistantBrief,
    SalesAssistantInput,
    SalesAssistantSummary,
    TalkTrack,
)


PERSONA_LABELS = {
    "ceo": "executive sponsor",
    "executive": "executive sponsor",
    "department_head": "department leader",
    "manager": "team manager",
    "field_leader": "field operations leader",
    "information_systems": "information systems owner",
    "quality_assurance": "quality assurance owner",
    "sales": "sales leader",
    "unknown": "stakeholder to be confirmed",
}

CATEGORY_LABELS = {
    "vision_ocr": "vision and OCR enabled operation",
    "automation": "automation and exception handling",
    "conversational_ai": "conversational AI operation",
    "knowledge_ai": "knowledge search and decision support",
    "crm_sales_intelligence": "CRM and sales intelligence",
    "generative_ai_transformation": "generative AI adoption",
    "digital_experience": "digital experience improvement",
    "generic_consulting": "business improvement discovery",
    "mixed": "multi-domain improvement",
}

STRATEGY_PHRASES = {
    "roi": "connect the discussion to investment logic and measurable business impact",
    "operational_improvement": "focus the discussion on workflow improvement and repeatable operations",
    "quality_improvement": "focus the discussion on quality stabilization and review consistency",
    "risk_reduction": "show how risk is reduced while preserving human confirmation",
    "digital_transformation": "position the proposal as a staged operating model change",
    "ai_enablement": "explain where AI assists people and where people retain decisions",
    "competitive_advantage": "connect the proposal to differentiation and faster customer response",
    "cost_reduction": "separate confirmed savings from hypotheses that require validation",
    "speed": "focus on cycle-time reduction and faster decisions",
    "customer_experience": "connect operational change to customer experience quality",
    "governance": "emphasize controlled adoption, auditability, and safe usage",
}

PERSONA_DECISION_POINTS = {
    "ceo": ["investment rationale", "business risk", "decision timing"],
    "executive": ["portfolio priority", "ROI hypothesis", "governance risk"],
    "department_head": ["department impact", "resource plan", "adoption risk"],
    "manager": ["team workflow", "implementation burden", "daily operation"],
    "field_leader": ["frontline workload", "exception handling", "training needs"],
    "information_systems": ["integration boundary", "security and access", "operation ownership"],
    "quality_assurance": ["quality criteria", "review traceability", "false-positive handling"],
    "sales": ["pipeline impact", "follow-up standardization", "customer visibility"],
    "unknown": ["decision process", "stakeholder map", "approval criteria"],
}

STAGE_OBJECTIVES = {
    MeetingStage.PREPARATION: "align the meeting objective and identify missing information before the customer conversation",
    MeetingStage.FIRST_MEETING: "confirm the business issue, decision process, and next discovery scope",
    MeetingStage.DISCOVERY: "validate current process, constraints, evidence, and success criteria",
    MeetingStage.PROPOSAL: "present the recommended direction and confirm what must be revised before approval",
    MeetingStage.NEGOTIATION: "clarify scope, constraints, risks, and decision conditions without overclaiming",
    MeetingStage.CLOSING: "confirm approval path, remaining blockers, and immediate next action",
    MeetingStage.FOLLOW_UP: "summarize decisions, open questions, and evidence required for the next step",
}

GUARDED_SECTION_KEYS = {
    "talk_track",
    "objection_handling",
    "decision_maker_support",
    "follow_up",
    "next_actions",
}


def generate_sales_assistant_brief(value: SalesAssistantInput) -> SalesAssistantBrief:
    brief = value.strategy_brief
    project_title = value.project_title or "Project title confirmation required"
    client_name = value.client_name or "Client name confirmation required"
    category = str(brief.project_category)
    persona = str(brief.primary_persona)
    decision_maker = str(brief.decision_maker)
    strategy = str(brief.primary_strategy)
    story = str(brief.story_type)
    meeting_stage = MeetingStage(value.meeting_stage)
    evidence = _evidence_items(value, brief)
    missing = _missing_items(value, brief)
    human_review_required, review_reasons = _review_gate(value, missing)

    summary = SalesAssistantSummary(
        project_title=project_title,
        client_name=client_name,
        category=category,
        persona=persona,
        decision_maker=decision_maker,
        strategy=strategy,
        story=story,
        sales_objective=f"prepare a customer conversation for {CATEGORY_LABELS.get(category, category)}",
        recommended_positioning=_recommended_positioning(category, strategy, persona),
        primary_message=brief.main_message,
        main_message=brief.main_message,
        confidence=brief.confidence,
        human_review_required=human_review_required,
        human_review_reasons=review_reasons,
        summary_notes=_summary_notes(value, missing),
    )
    meeting_plan = _meeting_plan(value, meeting_stage, category, strategy, persona)
    discovery_questions = _discovery_questions(missing, category, persona, decision_maker)
    talk_track = _talk_track(value, category, strategy, story)
    objections = _objections(category, strategy)
    decision_support = _decision_maker_support(decision_maker, missing)
    evidence_guidance = _evidence_guidance(value, evidence, missing)
    next_actions = _next_actions(category, missing)
    follow_up = _follow_up(value, next_actions, missing)
    risk = RiskAndGuardrails(
        review_severity=_severity(human_review_required, brief.confidence, missing),
        allowed_terms=list(brief.allowed_terms),
        conditional_terms=list(brief.conditional_terms),
        guardrails=_guardrails(missing),
        human_review_reasons=review_reasons,
        prohibited_terms=list(brief.prohibited_terms),
        unsupported_claims=_unsupported_claims(missing),
        compliance_notes=_compliance_notes(value, missing),
        removed_or_replaced_terms=[],
    )
    metadata = GenerationMetadata(
        strategy_brief_version=brief.schema_version,
        source_strategy_schema_version=brief.schema_version,
        source_strategy_confidence=brief.confidence,
        selected_rules=[
            f"category:{category}",
            f"persona:{persona}",
            f"decision_maker:{decision_maker}",
            f"strategy:{strategy}",
            f"story:{story}",
            f"meeting_stage:{meeting_stage.value}",
        ],
        warnings=_warnings(value, missing),
        fallback_reasons=_fallback_reasons(value, missing),
    )
    result = SalesAssistantBrief(
        summary=summary,
        meeting_plan=meeting_plan,
        discovery_questions=discovery_questions,
        talk_track=talk_track,
        objection_handling=objections,
        decision_maker_support=decision_support,
        evidence_guidance=evidence_guidance,
        next_actions=next_actions,
        follow_up=follow_up,
        risk_and_guardrails=risk,
        generation_metadata=metadata,
    )
    return _apply_term_guard(result, value)


def _label(value: str, labels: Dict[str, str]) -> str:
    return labels.get(value, value.replace("_", " "))


def _recommended_positioning(category: str, strategy: str, persona: str) -> str:
    return (
        f"Position the proposal as {CATEGORY_LABELS.get(category, category)} for "
        f"the {PERSONA_LABELS.get(persona, persona)}, and {STRATEGY_PHRASES.get(strategy, 'confirm decision criteria')}."
    )


def _evidence_items(value: SalesAssistantInput, brief) -> List[str]:
    items = list(value.evidence_items)
    for key, level in sorted(brief.evidence_summary.items()):
        if str(level) in {"confirmed", "provided"}:
            items.append(f"{key}: {level}")
    return _dedupe(items)


def _missing_items(value: SalesAssistantInput, brief) -> List[str]:
    missing = list(brief.missing_information)
    if not value.project_summary:
        missing.append("project_summary")
    if not value.budget_information:
        missing.append("budget_information")
    if not value.schedule_information:
        missing.append("schedule_information")
    if not value.client_name:
        missing.append("client_name")
    if not value.evidence_items:
        missing.append("customer_evidence")
    return _dedupe(missing)


def _review_gate(value: SalesAssistantInput, missing: List[str]) -> Tuple[bool, List[str]]:
    reasons = list(value.strategy_brief.human_review_reasons)
    if value.strategy_brief.human_review_required:
        reasons.append("source strategy brief requires human review")
    if value.strategy_brief.confidence < 0.62:
        reasons.append("source strategy confidence is below review threshold")
    if missing:
        reasons.append("missing information must be confirmed before customer-facing use")
    if value.strategy_brief.prohibited_terms and find_prohibited_terms(_source_text(value), value.strategy_brief.prohibited_terms):
        reasons.append("source input contains terms outside the selected strategy scope")
    return bool(reasons), _dedupe(reasons)


def _summary_notes(value: SalesAssistantInput, missing: List[str]) -> List[str]:
    notes = []
    if value.known_requirements:
        notes.append("known requirements are treated as customer-provided context")
    if value.known_constraints:
        notes.append("known constraints should be confirmed in the meeting")
    if missing:
        notes.append("some information is insufficient and must be handled as a hypothesis")
    return notes or ["brief is generated for sales preparation and requires human review before external use"]


def _meeting_plan(value: SalesAssistantInput, stage: MeetingStage, category: str, strategy: str, persona: str) -> MeetingPlan:
    strategy_phrase = STRATEGY_PHRASES.get(strategy, "confirm the customer's decision criteria")
    return MeetingPlan(
        meeting_stage=stage,
        recommended_duration_minutes=50,
        objective=STAGE_OBJECTIVES[stage],
        opening=(
            f"Today we will confirm the {CATEGORY_LABELS.get(category, category)} opportunity, "
            f"then {strategy_phrase} for the {PERSONA_LABELS.get(persona, persona)}."
        ),
        agenda=[
            "confirm current situation and decision background",
            "validate requirements, constraints, budget, and schedule",
            "agree on evidence needed for the next proposal step",
            "confirm owner and timing for the next action",
        ],
        desired_outcome="confirmed decision process, missing information, and next proposal action",
        next_step_goal="agree on evidence owners and the next proposal revision timing",
        success_criteria=[
            "decision maker and approval path are clear",
            "missing information is either confirmed or assigned",
            "next action has an owner and due hint",
        ],
        time_allocation_minutes={"context": 5, "discovery": 20, "proposal_direction": 15, "next_actions": 10},
    )


def _discovery_questions(missing: List[str], category: str, persona: str, decision_maker: str) -> List[DiscoveryQuestion]:
    category_label = _label(category, CATEGORY_LABELS)
    persona_label = _label(persona, PERSONA_LABELS)
    questions = [
        DiscoveryQuestion(
            id="q1",
            priority=QuestionPriority.HIGH,
            question=f"What business outcome should the {category_label} initiative prioritize first?",
            purpose="align the proposal with the customer's primary success condition",
            target_persona=persona,
            required=True,
            follow_up_questions=["What current baseline can be used?", "Who confirms the success criteria?"],
            linked_strategy_field="primary_strategy",
        ),
        DiscoveryQuestion(
            id="q2",
            priority=QuestionPriority.HIGH,
            question=f"Who will approve the next step, and how should we support the {PERSONA_LABELS.get(decision_maker, decision_maker)}?",
            purpose="confirm decision maker and approval criteria",
            target_persona=decision_maker,
            required=True,
            follow_up_questions=["What material is required for approval?", "When is the next decision timing?"],
            linked_strategy_field="decision_maker",
        ),
        DiscoveryQuestion(
            id="q3",
            priority=QuestionPriority.MEDIUM,
            question=f"Which current workflow should the {persona_label} see improved first?",
            purpose="connect the story to daily operation and adoption risk",
            target_persona=persona,
            required=False,
            follow_up_questions=["Which team owns this workflow?", "What exceptions happen most often?"],
            linked_strategy_field="primary_persona",
        ),
    ]
    for index, item in enumerate(missing[:4], start=4):
        questions.append(
            DiscoveryQuestion(
                id=f"q{index}",
                priority=QuestionPriority.HIGH if item in {"budget_information", "schedule_information"} else QuestionPriority.MEDIUM,
                question=f"Please confirm {item.replace('_', ' ')} before the proposal is finalized.",
                purpose="prevent unsupported claims and keep the next proposal evidence-based",
                target_persona=decision_maker,
                required=True,
                follow_up_questions=["Who can provide this information?", "Can it be confirmed before the next proposal version?"],
                linked_strategy_field=item,
            )
        )
    return questions


def _talk_track(value: SalesAssistantInput, category: str, strategy: str, story: str) -> TalkTrack:
    category_label = _label(category, CATEGORY_LABELS)
    strategy_phrase = STRATEGY_PHRASES.get(strategy, "confirm decision criteria")
    problem = value.project_summary or "current situation confirmation required"
    return TalkTrack(
        opening_talk=(
            f"This discussion is about {category_label} for {value.client_name or 'the client'}, "
            "with human review kept in the process."
        ),
        problem_confirmation=f"Confirm whether this current issue is accurate: {problem}.",
        proposal_explanation=f"Explain the proposal through the {story.replace('_', ' ')} story and avoid unsupported claims.",
        value_explanation=f"The value hypothesis is to {strategy_phrase}; confirm evidence before using numbers.",
        differentiation_talk="Differentiate by showing a controlled next step, clear review points, and evidence-based follow-up.",
        budget_talk="Treat budget as confirmation required unless the customer has provided a confirmed range.",
        schedule_talk="Treat schedule as confirmation required until dependencies and client-side preparation are clear.",
        closing_talk="Confirm the next action, owner, and evidence required for the next proposal version.",
        opening_message=(
            f"This discussion is about {category_label} for {value.client_name or 'the client'}, "
            "not about replacing human judgment without confirmation."
        ),
        story_beats=[
            f"Start with the current issue: {problem}.",
            f"Explain the proposed direction using the {story.replace('_', ' ')} story.",
            f"Use the strategy brief to {strategy_phrase}.",
            "Separate confirmed facts from hypotheses that still need customer confirmation.",
        ],
        transition_phrases=[
            "Before discussing a solution, let us confirm the operational facts.",
            "The next point is a hypothesis until the customer confirms the evidence.",
            "If this is correct, the next step is to define a limited validation scope.",
        ],
        closing_message="Close by confirming the next action, owner, and evidence required for the next proposal version.",
    )


def _objections(category: str, strategy: str) -> List[ObjectionHandlingItem]:
    items = [
        ObjectionHandlingItem(
            objection_type=ObjectionType.PRICE,
            expected_objection="The budget may be difficult to justify.",
            likely_objection="The budget may be difficult to justify.",
            recommended_response=(
                "Do not promise savings. Confirm the budget range, then propose a validation scope "
                "that can measure impact before a larger decision."
            ),
            supporting_evidence=["budget range", "scope assumptions", "evaluation criteria"],
            evidence_to_prepare=["budget range", "scope assumptions", "evaluation criteria"],
            prohibited_claims=["unsupported ROI promise", "unconfirmed fixed-price promise"],
            escalation_required=False,
            avoid_saying=["unsupported ROI promise", "unconfirmed fixed-price promise"],
        ),
        ObjectionHandlingItem(
            objection_type=ObjectionType.SCHEDULE,
            expected_objection="The requested schedule may be too tight.",
            likely_objection="The requested schedule may be too tight.",
            recommended_response="Separate must-have scope from optional scope and confirm the first decision milestone.",
            supporting_evidence=["target schedule", "dependency list", "client-side preparation tasks"],
            evidence_to_prepare=["target schedule", "dependency list", "client-side preparation tasks"],
            prohibited_claims=["unsupported schedule-risk denial"],
            escalation_required=False,
            avoid_saying=["unsupported schedule-risk denial"],
        ),
        ObjectionHandlingItem(
            objection_type=ObjectionType.EFFECTIVENESS,
            expected_objection="The expected effect is uncertain.",
            likely_objection="The expected effect is uncertain.",
            recommended_response="Treat the effect as a hypothesis and agree on how it will be measured during validation.",
            supporting_evidence=["current baseline", "measurement method", "sample data"],
            evidence_to_prepare=["current baseline", "measurement method", "sample data"],
            prohibited_claims=["unsupported certainty claim"],
            escalation_required=True,
            avoid_saying=["unsupported certainty claim"],
        ),
    ]
    if category in {"vision_ocr", "generative_ai_transformation", "knowledge_ai", "conversational_ai"}:
        items.append(
            ObjectionHandlingItem(
                objection_type=ObjectionType.OPERATION,
                expected_objection="AI output may be trusted too much or used incorrectly.",
                likely_objection="AI output may be trusted too much or used incorrectly.",
                recommended_response="Keep human confirmation in the process and define escalation rules before operation starts.",
                supporting_evidence=["review workflow", "acceptance criteria", "operation owner"],
                evidence_to_prepare=["review workflow", "acceptance criteria", "operation owner"],
                prohibited_claims=["fully automatic decision", "human review is unnecessary"],
                escalation_required=True,
                avoid_saying=["fully automatic decision", "human review is unnecessary"],
            )
        )
    if strategy in {"governance", "risk_reduction"}:
        items.append(
            ObjectionHandlingItem(
                objection_type=ObjectionType.SECURITY,
                expected_objection="Security or governance approval may take time.",
                likely_objection="Security or governance approval may take time.",
                recommended_response="Confirm access boundaries, logging needs, and approval owners early in the meeting.",
                supporting_evidence=["security requirements", "data handling policy", "approval owner"],
                evidence_to_prepare=["security requirements", "data handling policy", "approval owner"],
                prohibited_claims=["security review can be skipped"],
                escalation_required=True,
                avoid_saying=["security review can be skipped"],
            )
        )
    return items


def _decision_maker_support(decision_maker: str, missing: List[str]) -> DecisionMakerSupport:
    points = PERSONA_DECISION_POINTS.get(decision_maker, PERSONA_DECISION_POINTS["unknown"])
    risks = ["approval criteria are not confirmed"] if decision_maker == "unknown" else []
    if missing:
        risks.append("missing information may delay approval")
    return DecisionMakerSupport(
        decision_maker=decision_maker,
        likely_decision_criteria=points,
        approval_barriers=risks,
        information_required_for_approval=[
            "confirmed budget range",
            "confirmed schedule constraint",
            "success criteria",
            "implementation owner",
        ],
        recommended_materials=["one-page summary", "scope and assumptions", "evidence gap list", "next-step plan"],
        internal_explanation_points=[
            "what is confirmed",
            "what is still a hypothesis",
            "what decision is requested next",
        ],
        decision_points=points,
        materials_to_prepare=["one-page summary", "scope and assumptions", "evidence gap list", "next-step plan"],
        approval_risks=risks,
    )


def _evidence_guidance(value: SalesAssistantInput, evidence: List[str], missing: List[str]) -> EvidenceGuidance:
    safe_claims = [
        "The proposal direction is based on the approved Strategy Brief.",
        "Unconfirmed numbers must be presented as hypotheses or confirmation items.",
    ]
    if value.evidence_items:
        safe_claims.append("Customer-provided evidence can be referenced after sales review.")
    return EvidenceGuidance(
        usable_evidence=evidence,
        conditional_evidence=["budget", "schedule", "impact", "integration scope"],
        missing_evidence=missing,
        claims_requiring_review=[
            "budget fit",
            "schedule feasibility",
            "expected impact",
            "integration scope",
        ],
        available_evidence=evidence,
        evidence_gaps=missing,
        safe_claims=safe_claims,
        claims_requiring_confirmation=[
            "budget fit",
            "schedule feasibility",
            "expected impact",
            "integration scope",
        ],
    )


def _next_actions(category: str, missing: List[str]) -> List[NextAction]:
    actions = [
        NextAction(
            id="a1",
            priority=ActionPriority.HIGH,
            owner=ActionOwner.SALES,
            action="send a meeting summary that separates confirmed facts from hypotheses",
            timing="after the meeting",
            completion_condition="customer receives a summary with confirmed facts and hypotheses separated",
            due_hint="after the meeting",
            reason="keeps the next proposal evidence-based",
        ),
        NextAction(
            id="a2",
            priority=ActionPriority.HIGH,
            owner=ActionOwner.CLIENT,
            action="confirm decision maker, budget range, and schedule constraint",
            timing="before next proposal revision",
            completion_condition="decision maker, budget range, and schedule constraint are confirmed or marked unknown",
            due_hint="before next proposal revision",
            reason="prevents unsupported assertions",
        ),
        NextAction(
            id="a3",
            priority=ActionPriority.MEDIUM,
            owner=ActionOwner.JOINT,
            action=f"agree on validation scope for {CATEGORY_LABELS.get(category, category)}",
            timing="next workshop",
            completion_condition="validation scope, owner, and acceptance criteria are agreed",
            due_hint="next workshop",
            reason="turns the strategy into an executable next step",
        ),
    ]
    if missing:
        actions.append(
            NextAction(
                id="a4",
                priority=ActionPriority.HIGH,
                owner=ActionOwner.SALES,
                action="list missing information and assign confirmation owners",
                timing="before external proposal use",
                completion_condition="missing information has an owner or is explicitly labeled as insufficient",
                due_hint="before external proposal use",
                reason="human review is required when information is insufficient",
            )
        )
    return actions


def _follow_up(value: SalesAssistantInput, actions: List[NextAction], missing: List[str]) -> FollowUp:
    subject = f"Next steps for {value.project_title or 'the proposal'}"
    action_lines = "\n".join(f"- {item.action} ({item.owner})" for item in actions[:4])
    missing_lines = "\n".join(f"- {item.replace('_', ' ')}" for item in missing[:6]) or "- no additional item recorded"
    body = (
        f"Thank you for the discussion about {value.project_title or 'the project'}.\n\n"
        "Based on the current Strategy Brief, the proposal direction is a working hypothesis until the remaining items are confirmed.\n\n"
        f"Next actions:\n{action_lines}\n\n"
        f"Items requiring confirmation:\n{missing_lines}\n\n"
        "We will update the proposal after these items are confirmed."
    )
    summary_template = (
        "Meeting summary:\n"
        "- Confirmed facts:\n"
        "- Hypotheses:\n"
        "- Open questions:\n"
        "- Next decision:\n"
    )
    return FollowUp(
        email_subject=subject,
        subject=subject,
        email_body=body,
        meeting_summary_template=summary_template,
        requested_client_actions=[item.action for item in actions if item.owner in {"client", "joint"}],
        internal_follow_up_actions=[item.action for item in actions if item.owner in {"sales", "manager", "technical"}],
        attachments_to_include=["strategy summary", "evidence gap list"],
        confirmation_items=missing,
    )


def _severity(review_required: bool, confidence: float, missing: List[str]) -> ReviewSeverity:
    if review_required and (confidence < 0.45 or len(missing) >= 5):
        return ReviewSeverity.HIGH
    if review_required:
        return ReviewSeverity.MEDIUM
    return ReviewSeverity.LOW


def _guardrails(missing: List[str]) -> List[str]:
    guardrails = [
        "do not invent customer facts, numbers, schedules, or approval conditions",
        "mark unconfirmed content as confirmation required, insufficient information, or hypothesis",
        "do not include credentials, tokens, passwords, or API keys in any output",
        "do not send this brief externally without human review",
    ]
    if missing:
        guardrails.append("missing information must be resolved or explicitly labeled before customer-facing use")
    return guardrails


def _unsupported_claims(missing: List[str]) -> List[str]:
    claims = [
        "business effect stated without evidence",
        "ROI stated without evidence",
        "price stated before scope confirmation",
        "schedule stated before dependency confirmation",
    ]
    if missing:
        claims.append("customer-specific fact that has not been confirmed")
    return claims


def _compliance_notes(value: SalesAssistantInput, missing: List[str]) -> List[str]:
    notes = [
        "Do not log or store credentials, tokens, passwords, or API keys.",
        "Use this brief internally until human review is complete.",
    ]
    if missing:
        notes.append("Missing items must be labeled as confirmation required or insufficient information.")
    if value.strategy_brief.prohibited_terms:
        notes.append("Term Guard is applied to guarded sales assistant sections.")
    return notes


def _fallback_reasons(value: SalesAssistantInput, missing: List[str]) -> List[str]:
    reasons = []
    if missing:
        reasons.append("missing supplemental sales input")
    if value.strategy_brief.human_review_required:
        reasons.append("source strategy brief requires human review")
    if value.strategy_brief.confidence < 0.62:
        reasons.append("source strategy confidence below threshold")
    return reasons


def _warnings(value: SalesAssistantInput, missing: List[str]) -> List[str]:
    warnings = []
    if missing:
        warnings.append("generated with missing information")
    if value.strategy_brief.human_review_required:
        warnings.append("source strategy brief requires review")
    if value.strategy_brief.prohibited_terms and find_prohibited_terms(_source_text(value), value.strategy_brief.prohibited_terms):
        warnings.append("source input contains terms outside the selected strategy scope")
    return warnings


def _source_text(value: SalesAssistantInput) -> str:
    parts = [
        value.project_title,
        value.project_summary,
        value.client_name,
        value.budget_information,
        value.schedule_information,
        *value.known_requirements,
        *value.known_constraints,
        *value.previous_interactions,
        *value.evidence_items,
    ]
    return " ".join(part for part in parts if part)


def _apply_term_guard(brief: SalesAssistantBrief, value: SalesAssistantInput) -> SalesAssistantBrief:
    prohibited = list(value.strategy_brief.prohibited_terms)
    if not prohibited:
        return brief
    data = brief.dict()
    changed_terms: List[str] = []
    for key in GUARDED_SECTION_KEYS:
        sanitized, terms = _sanitize_value(data.get(key), prohibited)
        data[key] = sanitized
        changed_terms.extend(terms)
    source_hits = find_prohibited_terms(_source_text(value), prohibited)
    changed_terms.extend(source_hits)
    changed_terms = _dedupe(changed_terms)
    if changed_terms:
        data["summary"]["human_review_required"] = True
        reasons = data["risk_and_guardrails"].setdefault("human_review_reasons", [])
        reasons.append("term guard replaced or removed out-of-scope terms")
        data["risk_and_guardrails"]["removed_or_replaced_terms"] = changed_terms
        warnings = data["generation_metadata"].setdefault("warnings", [])
        warnings.append("term guard applied to guarded sales assistant sections")
    return SalesAssistantBrief(**data)


def _sanitize_value(value: Any, prohibited: List[str]) -> Tuple[Any, List[str]]:
    if isinstance(value, str):
        hits = find_prohibited_terms(value, prohibited)
        sanitized = value
        for term in hits:
            sanitized = _replace_case_insensitive(sanitized, term, "review-required category term")
        return sanitized, hits
    if isinstance(value, list):
        result = []
        all_hits: List[str] = []
        for item in value:
            sanitized, hits = _sanitize_value(item, prohibited)
            result.append(sanitized)
            all_hits.extend(hits)
        return result, all_hits
    if isinstance(value, dict):
        result: Dict[str, Any] = {}
        all_hits = []
        for key, item in value.items():
            sanitized, hits = _sanitize_value(item, prohibited)
            result[key] = sanitized
            all_hits.extend(hits)
        return result, all_hits
    return value, []


def _replace_case_insensitive(text: str, term: str, replacement: str) -> str:
    lower = text.lower()
    needle = term.lower()
    start = 0
    pieces: List[str] = []
    while True:
        index = lower.find(needle, start)
        if index == -1:
            pieces.append(text[start:])
            break
        pieces.append(text[start:index])
        pieces.append(replacement)
        start = index + len(term)
    return "".join(pieces)


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        text = str(item).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def brief_to_canonical_json(brief: SalesAssistantBrief) -> str:
    return json.dumps(brief.dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
