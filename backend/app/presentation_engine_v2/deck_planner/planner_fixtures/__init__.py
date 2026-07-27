"""Synthetic Proposal Context fixtures for the Phase 2A Deck Planner."""

from __future__ import annotations

import copy
from typing import Any


def _case(
    case_id: str,
    project_name: str,
    summary: str,
    *,
    industry: str,
    category: str,
    decision_maker: str,
    persona: str,
    purpose: str,
    problems: list[str],
    outcomes: list[str],
    budget: str | None = None,
    competition: str | None = None,
    timeline: str | None = None,
) -> dict[str, Any]:
    return {
        "project_id": f"planner-fixture-{case_id}",
        "project_name": project_name,
        "project_summary": summary,
        "industry": industry,
        "proposal_category": category,
        "competitive_information": competition,
        "budget_range": budget,
        "decision_maker": decision_maker,
        "persona": persona,
        "implementation_purpose": purpose,
        "problems": problems,
        "expected_outcomes": outcomes,
        "timeline": timeline,
        "language": "ja",
    }


VALID_PLANNER_CONTEXTS: list[dict[str, Any]] = [
    _case(
        "web-01",
        "Manufacturing Website Renewal",
        "Renew a corporate website to improve lead quality and product understanding.",
        industry="Manufacturing",
        category="Web production",
        decision_maker="Marketing department head",
        persona="Marketing manager",
        purpose="Improve customer acquisition and product explanation.",
        problems=["Product strengths are hard to understand", "Inquiry quality is inconsistent"],
        outcomes=["Higher qualified inquiries", "Clearer product story"],
        budget="8M to 12M JPY",
        competition="Alternative web agencies are being compared.",
        timeline="Launch in six months",
    ),
    _case(
        "ai-vision-01",
        "Flower Auction Image Recognition PoC",
        "Use AI image recognition to support flower type, color, grade, and condition checking.",
        industry="Wholesale",
        category="AI image recognition",
        decision_maker="Operations executive",
        persona="Quality assurance and operations leaders",
        purpose="Reduce manual checking effort while keeping human final review.",
        problems=["Manual image checking delays peak operations", "Classification quality depends on staff experience"],
        outcomes=["Shorter checking time", "Clear PoC accuracy criteria", "Reusable review history"],
        budget="Up to 10M JPY",
        competition="Internal manual operation remains the default alternative.",
        timeline="Target introduction around May 2027",
    ),
    _case(
        "ocr-01",
        "Invoice AI-OCR Introduction",
        "Introduce AI-OCR to read invoice images and connect results to the accounting workflow.",
        industry="Back office",
        category="AI-OCR",
        decision_maker="Finance department head",
        persona="Accounting manager",
        purpose="Reduce manual invoice entry and checking workload.",
        problems=["Manual entry takes time", "Correction history is not reusable"],
        outcomes=["Lower data entry time", "Measured recognition accuracy", "Clear exception handling"],
        budget="PoC budget available",
        timeline="PoC in Q2",
    ),
    _case(
        "rpa-01",
        "Order Entry Automation",
        "Automate repetitive order entry and status update tasks with RPA.",
        industry="Retail",
        category="RPA automation",
        decision_maker="Operations manager",
        persona="Field leader",
        purpose="Stabilize back-office processing during peak periods.",
        problems=["Manual copy-and-paste work is frequent", "Processing delay increases during campaigns"],
        outcomes=["Reduced manual operation time", "Fewer status update delays"],
        budget="5M JPY range",
    ),
    _case(
        "crm-01",
        "CRM Pipeline Visibility",
        "Introduce CRM/SFA usage rules to improve pipeline visibility and follow-up quality.",
        industry="SaaS",
        category="CRM SFA",
        decision_maker="Sales director",
        persona="Sales manager",
        purpose="Improve sales management and forecast accuracy.",
        problems=["Sales activity is scattered", "Forecasts depend on individual reports"],
        outcomes=["Pipeline visibility", "Higher follow-up consistency"],
        budget="Annual subscription budget under review",
        competition="Existing spreadsheet operation is the main alternative.",
    ),
    _case(
        "dx-01",
        "Factory DX Roadmap",
        "Create a DX roadmap for production reporting and daily operations.",
        industry="Manufacturing",
        category="DX",
        decision_maker="Plant manager",
        persona="Factory operations leader",
        purpose="Improve decision speed using shared operational data.",
        problems=["Reports are created manually", "Daily status is hard to compare"],
        outcomes=["Standardized reporting", "Faster issue escalation"],
        timeline="Start small in the next quarter",
    ),
    _case(
        "chatbot-01",
        "Customer Support AI Chatbot",
        "Deploy an AI chatbot to support first-response handling and FAQ routing.",
        industry="Customer support",
        category="AI chatbot",
        decision_maker="Support department head",
        persona="Support operations manager",
        purpose="Reduce repetitive inquiries and improve response consistency.",
        problems=["Similar inquiries are repeated", "New staff need time to answer correctly"],
        outcomes=["Lower first response load", "More consistent answers"],
        budget="Initial PoC budget defined",
    ),
    _case(
        "knowledge-01",
        "Internal Knowledge Search",
        "Build internal knowledge search over manuals, proposals, and support documents.",
        industry="IT services",
        category="Generative AI knowledge search",
        decision_maker="Information systems manager",
        persona="Information systems and operations",
        purpose="Make internal knowledge easier to find and reuse.",
        problems=["Documents are scattered", "Experienced staff are asked the same questions"],
        outcomes=["Faster search", "Improved reuse of approved materials"],
    ),
    _case(
        "ec-01",
        "EC Growth Improvement",
        "Improve EC purchase flow, product pages, and campaign landing pages.",
        industry="Retail",
        category="EC website",
        decision_maker="EC business owner",
        persona="Marketing manager",
        purpose="Increase online sales and campaign performance.",
        problems=["Drop-off is high", "Product value is hard to compare"],
        outcomes=["Improved conversion", "Clearer product discovery"],
        budget="10M JPY range",
        competition="Several agencies are under comparison.",
    ),
    _case(
        "hiring-01",
        "Recruiting Site Renewal",
        "Renew recruiting content to improve candidate understanding and entry quality.",
        industry="Human resources",
        category="Hiring branding",
        decision_maker="HR department head",
        persona="Recruiting manager",
        purpose="Improve candidate quality and reduce mismatch.",
        problems=["Job appeal is not clear", "Candidate questions repeat in interviews"],
        outcomes=["Better candidate understanding", "Improved interview efficiency"],
        competition="Recruitment media improvement is also considered.",
    ),
    _case(
        "branding-01",
        "Corporate Brand Refresh",
        "Refresh corporate message and sales materials for a new market segment.",
        industry="Professional services",
        category="Branding",
        decision_maker="CEO",
        persona="Executive",
        purpose="Clarify positioning for a new target market.",
        problems=["Positioning is hard to explain", "Sales materials vary by person"],
        outcomes=["Consistent message", "Better executive-level first impression"],
        budget="Executive approval required",
    ),
    _case(
        "saas-01",
        "SaaS Onboarding Improvement",
        "Improve onboarding process for a BtoB SaaS product.",
        industry="SaaS",
        category="Customer success DX",
        decision_maker="Customer success director",
        persona="CS manager",
        purpose="Shorten time to value and reduce onboarding workload.",
        problems=["Onboarding differs by担当", "Users stop before setup completion"],
        outcomes=["Shorter onboarding time", "Higher activation rate"],
    ),
    _case(
        "medical-01",
        "Clinic Reservation Workflow",
        "Improve reservation and reminder operations for clinics.",
        industry="Medical",
        category="Workflow automation",
        decision_maker="Clinic owner",
        persona="Operations lead",
        purpose="Reduce phone workload and missed appointments.",
        problems=["Phone calls concentrate at specific times", "Reminder operation is manual"],
        outcomes=["Lower phone workload", "Fewer missed appointments"],
        budget="Small pilot budget",
    ),
    _case(
        "education-01",
        "Learning Progress Dashboard",
        "Create a dashboard to visualize learner progress and support interventions.",
        industry="Education",
        category="DX dashboard",
        decision_maker="School executive",
        persona="Education manager",
        purpose="Improve learning support decisions.",
        problems=["Progress differs by class", "Interventions are late"],
        outcomes=["Earlier intervention", "Shared progress view"],
    ),
    _case(
        "construction-01",
        "Construction Site Report Automation",
        "Digitize site reports and automate daily summary creation.",
        industry="Construction",
        category="Automation DX",
        decision_maker="Site operations head",
        persona="Field leader",
        purpose="Reduce report workload and improve field visibility.",
        problems=["Daily reports are duplicated", "Photos and comments are hard to search"],
        outcomes=["Shorter report creation time", "Improved site status sharing"],
    ),
    _case(
        "realestate-01",
        "Real Estate Lead Management",
        "Improve lead follow-up and property matching using CRM operations.",
        industry="Real estate",
        category="CRM",
        decision_maker="Sales department head",
        persona="Sales manager",
        purpose="Improve lead response speed and proposal quality.",
        problems=["Follow-up timing varies", "Property recommendations are not logged"],
        outcomes=["Faster follow-up", "Higher matching quality"],
        competition="Existing CRM customization is being compared.",
    ),
    _case(
        "logistics-01",
        "Logistics Routing Optimization PoC",
        "Evaluate data-driven routing recommendations for daily delivery planning.",
        industry="Logistics",
        category="AI optimization",
        decision_maker="Operations executive",
        persona="Logistics manager",
        purpose="Improve route planning quality and reduce rework.",
        problems=["Route planning depends on experienced staff", "Last-minute changes are hard to handle"],
        outcomes=["Reduced planning rework", "Clear evaluation criteria"],
        budget="PoC budget under review",
    ),
    _case(
        "finance-01",
        "Expense Review Automation",
        "Use rules and AI support to classify expenses and flag exceptions.",
        industry="Finance",
        category="AI automation",
        decision_maker="CFO",
        persona="Finance executive",
        purpose="Improve compliance and reduce checking workload.",
        problems=["Exception checking takes time", "Audit trail quality differs"],
        outcomes=["Better exception detection", "More consistent review trail"],
        budget="Approval needed",
    ),
    _case(
        "security-01",
        "Security Assessment Workflow",
        "Standardize security assessment workflow and reporting.",
        industry="IT",
        category="DX workflow",
        decision_maker="Information systems executive",
        persona="Security manager",
        purpose="Reduce assessment delays and improve governance.",
        problems=["Assessment requests pile up", "Evidence collection is manual"],
        outcomes=["Shorter review cycle", "Standardized evidence"],
    ),
    _case(
        "sales-training-01",
        "Sales Enablement Knowledge Pack",
        "Create reusable sales enablement materials and searchable proposal examples.",
        industry="Sales",
        category="Knowledge AI",
        decision_maker="Sales director",
        persona="Sales enablement manager",
        purpose="Improve new sales staff ramp-up and proposal consistency.",
        problems=["Good examples are hard to find", "Training depends on senior staff"],
        outcomes=["Faster ramp-up", "More consistent proposal quality"],
    ),
    _case(
        "investor-01",
        "New Service Investment Review",
        "Prepare an executive proposal for a new service investment decision.",
        industry="Technology",
        category="Investment DX",
        decision_maker="CEO",
        persona="Executive committee",
        purpose="Decide whether to start the next investment phase.",
        problems=["Market opportunity is not organized", "Risk and cost are not comparable"],
        outcomes=["Clear investment criteria", "Decision-ready roadmap"],
        budget="Board approval required",
        competition="Competitors are moving into adjacent services.",
    ),
    _case(
        "procurement-01",
        "Vendor Selection Proposal",
        "Compare implementation partners for a workflow modernization project.",
        industry="Enterprise",
        category="Vendor comparison",
        decision_maker="Procurement manager",
        persona="Procurement and department heads",
        purpose="Select a partner based on fit, risk, and value.",
        problems=["Evaluation criteria are unclear", "Price and value are hard to compare"],
        outcomes=["Clear vendor comparison", "Lower selection risk"],
        budget="Procurement budget defined",
        competition="Multiple vendors are being compared.",
    ),
    _case(
        "startup-01",
        "Startup Sales Material Refresh",
        "Improve sales deck structure for a startup entering enterprise sales.",
        industry="Startup",
        category="Sales material",
        decision_maker="Founder",
        persona="Founder and sales lead",
        purpose="Make enterprise value easier to explain.",
        problems=["Story changes by meeting", "Enterprise concerns are not addressed"],
        outcomes=["More consistent story", "Better objection handling"],
    ),
    _case(
        "agency-01",
        "Agency Proposal Standardization",
        "Standardize proposal creation process across project managers.",
        industry="Agency",
        category="Proposal DX",
        decision_maker="Department head",
        persona="Project managers",
        purpose="Improve proposal quality and reduce creation time.",
        problems=["Proposal quality differs by creator", "Reusable knowledge is scattered"],
        outcomes=["Shorter creation time", "More stable proposal quality"],
    ),
    _case(
        "retail-store-01",
        "Store Operation Improvement",
        "Improve store task management and shift communication.",
        industry="Retail",
        category="Workflow automation",
        decision_maker="Store operations manager",
        persona="Field leader",
        purpose="Reduce missed tasks and improve handover quality.",
        problems=["Tasks are not visible", "Handover notes vary by staff"],
        outcomes=["Fewer missed tasks", "Clearer daily operations"],
    ),
    _case(
        "manufacturing-qa-01",
        "Quality Inspection Data Platform",
        "Create a data platform for inspection logs and defect analysis.",
        industry="Manufacturing",
        category="DX analytics",
        decision_maker="Quality assurance head",
        persona="Quality manager",
        purpose="Improve quality analysis speed and traceability.",
        problems=["Inspection logs are separate", "Defect trends are hard to see"],
        outcomes=["Faster root-cause analysis", "Better traceability"],
        budget="Mid-size project budget",
    ),
    _case(
        "travel-01",
        "Travel Customer Support Automation",
        "Automate repetitive travel inquiry handling and escalation routing.",
        industry="Travel",
        category="AI chatbot",
        decision_maker="Support manager",
        persona="Customer support leader",
        purpose="Reduce repeated inquiry workload.",
        problems=["Peak inquiries overwhelm staff", "Escalation rules are not standardized"],
        outcomes=["Lower response load", "Clear escalation quality"],
    ),
    _case(
        "insurance-01",
        "Insurance Document Classification",
        "Classify submitted documents and route exceptions for review.",
        industry="Insurance",
        category="AI-OCR document classification",
        decision_maker="Operations executive",
        persona="Back-office operations",
        purpose="Reduce document sorting and checking workload.",
        problems=["Document types vary", "Manual routing causes delay"],
        outcomes=["Faster classification", "Lower routing error"],
        budget="PoC first",
    ),
    _case(
        "restaurant-01",
        "Restaurant Reservation Optimization",
        "Improve reservation operations and campaign follow-up.",
        industry="Restaurant",
        category="CRM automation",
        decision_maker="Business owner",
        persona="Store manager",
        purpose="Improve repeat visits and reduce manual follow-up.",
        problems=["Reservation history is not used", "Follow-up messages are manual"],
        outcomes=["More repeat visits", "Lower follow-up workload"],
    ),
    _case(
        "generic-01",
        "Operations Improvement Proposal",
        "Improve daily operations by organizing issues, process, responsibilities, and success criteria.",
        industry="General business",
        category="Business improvement",
        decision_maker="Department manager",
        persona="Mixed business audience",
        purpose="Agree on improvement priorities and next action.",
        problems=["Current issues are not prioritized", "Next actions are unclear"],
        outcomes=["Clearer priorities", "Actionable next meeting agenda"],
    ),
]


def valid_context_payloads() -> list[dict[str, Any]]:
    return copy.deepcopy(VALID_PLANNER_CONTEXTS)


def invalid_context_payloads() -> list[dict[str, Any]]:
    base = valid_context_payloads()[0]
    invalid: list[dict[str, Any]] = []

    missing_summary = copy.deepcopy(base)
    missing_summary.pop("project_summary")
    invalid.append(missing_summary)

    empty_summary = copy.deepcopy(base)
    empty_summary["project_summary"] = ""
    invalid.append(empty_summary)

    bad_problems = copy.deepcopy(base)
    bad_problems["problems"] = ["problem"] * 20
    invalid.append(bad_problems)

    bad_outcomes = copy.deepcopy(base)
    bad_outcomes["expected_outcomes"] = ["outcome"] * 20
    invalid.append(bad_outcomes)

    long_summary = copy.deepcopy(base)
    long_summary["project_summary"] = "x" * 1300
    invalid.append(long_summary)

    bad_extra = copy.deepcopy(base)
    bad_extra["unknown"] = "not allowed"
    invalid.append(bad_extra)

    bad_language = copy.deepcopy(base)
    bad_language["language"] = "j"
    invalid.append(bad_language)

    long_project_name = copy.deepcopy(base)
    long_project_name["project_name"] = "x" * 200
    invalid.append(long_project_name)

    long_decision_maker = copy.deepcopy(base)
    long_decision_maker["decision_maker"] = "x" * 140
    invalid.append(long_decision_maker)

    long_project_id = copy.deepcopy(base)
    long_project_id["project_id"] = "x" * 140
    invalid.append(long_project_id)

    long_timeline = copy.deepcopy(base)
    long_timeline["timeline"] = "x" * 200
    invalid.append(long_timeline)

    long_budget = copy.deepcopy(base)
    long_budget["budget_range"] = "x" * 200
    invalid.append(long_budget)

    return invalid
