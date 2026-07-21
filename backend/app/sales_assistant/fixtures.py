from dataclasses import dataclass
from typing import Dict, List

from app.strategy_engine.evaluator import evaluate_strategy
from app.strategy_engine.fixtures import FIXTURES as STRATEGY_FIXTURES
from app.strategy_engine.models import ProposalStrategyInput

from .enums import MeetingStage
from .models import SalesAssistantInput


@dataclass(frozen=True)
class SalesAssistantFixture:
    name: str
    strategy_input: ProposalStrategyInput
    meeting_stage: MeetingStage
    client_name: str
    known_requirements: List[str]
    known_constraints: List[str]
    budget_information: str
    schedule_information: str
    previous_interactions: List[str]
    evidence_items: List[str]


def _base(name: str, strategy_key: str, **overrides) -> SalesAssistantFixture:
    strategy_input = overrides.pop("strategy_input", STRATEGY_FIXTURES[strategy_key])
    return SalesAssistantFixture(
        name=name,
        strategy_input=strategy_input,
        meeting_stage=overrides.pop("meeting_stage", MeetingStage.DISCOVERY),
        client_name=overrides.pop("client_name", "Sample Client"),
        known_requirements=overrides.pop("known_requirements", ["scope confirmation", "operation owner confirmation"]),
        known_constraints=overrides.pop("known_constraints", ["final scope is not confirmed"]),
        budget_information=overrides.pop("budget_information", "budget range confirmation required"),
        schedule_information=overrides.pop("schedule_information", "target schedule confirmation required"),
        previous_interactions=overrides.pop("previous_interactions", ["initial conversation completed"]),
        evidence_items=overrides.pop("evidence_items", ["customer-provided issue summary"]),
    )


EXTRA_INPUTS: Dict[str, ProposalStrategyInput] = {
    "ec": ProposalStrategyInput(
        project_title="EC operation improvement",
        project_summary="Customer wants to reduce manual order checks and improve repeat-purchase visibility.",
        business_goals=["reduce manual checks", "increase repeat purchase insight"],
        current_problems=["order data is fragmented", "manual checking delays shipment"],
        proposed_solution="workflow redesign and dashboard for operation review",
        expected_deliverables=["operation design", "dashboard", "training"],
        expected_kpis=["manual check time", "repeat purchase visibility"],
        stakeholders=["department_head", "operations manager"],
    ),
    "recruitment": ProposalStrategyInput(
        project_title="Recruiting site and candidate journey improvement",
        project_summary="Customer wants to improve candidate understanding and application conversion.",
        business_goals=["candidate experience", "application conversion"],
        current_problems=["information is scattered", "candidate flow is unclear"],
        proposed_solution="digital experience renewal with content governance",
        expected_deliverables=["site renewal", "content structure", "operation guide"],
        expected_kpis=["application conversion", "content update frequency"],
        stakeholders=["recruiting", "communications"],
    ),
    "admin_proposal": ProposalStrategyInput(
        project_title="Administrative workflow standardization",
        project_summary="Customer wants to standardize approval and document handling across departments.",
        business_goals=["standardize workflow", "reduce handoff mistakes"],
        current_problems=["approval paths differ by team", "document versions are unclear"],
        proposed_solution="workflow design and staged operation rules",
        expected_deliverables=["workflow map", "approval rules", "operation manual"],
        expected_kpis=["handoff errors", "approval lead time"],
        stakeholders=["manager", "department_head"],
    ),
}


SALES_ASSISTANT_FIXTURES: Dict[str, SalesAssistantFixture] = {
    "web_creation": _base("web_creation", "web_renewal", meeting_stage=MeetingStage.FIRST_MEETING),
    "ec": _base("ec", "generic_consulting", strategy_input=EXTRA_INPUTS["ec"]),
    "recruitment": _base("recruitment", "generic_consulting", strategy_input=EXTRA_INPUTS["recruitment"]),
    "operations": _base("operations", "generic_consulting"),
    "ai_adoption": _base("ai_adoption", "generative_ai", meeting_stage=MeetingStage.PROPOSAL),
    "system_development": _base("system_development", "it_security"),
    "branding": _base("branding", "generic_consulting"),
    "marketing": _base("marketing", "crm"),
    "other_unclear": _base("other_unclear", "sparse", client_name="", evidence_items=[]),
    "budget_unknown": _base("budget_unknown", "budget_only", budget_information="", evidence_items=[]),
    "schedule_unknown": _base("schedule_unknown", "ai_ocr", schedule_information="", evidence_items=["invoice sample exists"]),
    "decision_maker_unknown": _base("decision_maker_unknown", "generic_consulting", previous_interactions=[]),
    "evidence_shortage": _base("evidence_shortage", "knowledge_search", evidence_items=[]),
    "low_confidence": _base("low_confidence", "sparse", budget_information="", schedule_information="", evidence_items=[]),
    "prohibited_term_input": _base(
        "prohibited_term_input",
        "prohibited_term_mixed",
        known_requirements=["AI-OCR scope only; CRM was mentioned by mistake"],
        evidence_items=["invoice sample exists"],
    ),
    "conditional_term_input": _base("conditional_term_input", "web_chatbot"),
    "human_review_required": _base("human_review_required", "ai_ocr_rpa", meeting_stage=MeetingStage.NEGOTIATION),
    "admin_proposal": _base("admin_proposal", "generic_consulting", strategy_input=EXTRA_INPUTS["admin_proposal"]),
    "field_persona": _base("field_persona", "field_operations"),
    "multi_persona": _base("multi_persona", "crm_generative_ai"),
    "image_recognition": _base("image_recognition", "image_recognition"),
    "chatbot": _base("chatbot", "chatbot"),
}


def build_sales_assistant_input(name: str) -> SalesAssistantInput:
    fixture = SALES_ASSISTANT_FIXTURES[name]
    strategy_brief = evaluate_strategy(fixture.strategy_input)
    return SalesAssistantInput(
        strategy_brief=strategy_brief,
        project_title=fixture.strategy_input.project_title,
        project_summary=fixture.strategy_input.project_summary,
        client_name=fixture.client_name,
        known_requirements=fixture.known_requirements,
        known_constraints=fixture.known_constraints,
        budget_information=fixture.budget_information,
        schedule_information=fixture.schedule_information,
        meeting_stage=fixture.meeting_stage,
        previous_interactions=fixture.previous_interactions,
        evidence_items=fixture.evidence_items,
    )


def fixture_names() -> List[str]:
    return sorted(SALES_ASSISTANT_FIXTURES.keys())
