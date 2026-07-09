import re

from app.models import ProposalRequest, PptxDownloadRequest


def proposal_input_length(payload: ProposalRequest) -> int:
    return sum(
        len(value or "")
        for value in [
            payload.project_brief,
            payload.client_company_info,
            payload.competitor_site_url,
            payload.competitor_company_name,
            payload.estimated_page_count,
            payload.cms_required,
            payload.contact_form_required,
            payload.special_function_required,
            payload.seo_required,
            payload.content_creation_required,
            payload.desired_launch_timing,
            payload.budget_range,
            payload.hearing_result,
            payload.own_service_info,
            payload.past_proposal_template,
            payload.case_studies,
        ]
    )


def pptx_input_length(payload: PptxDownloadRequest) -> int:
    return sum(
        len(value or "")
        for value in [
            payload.project_brief,
            payload.client_company_info,
            payload.competitor_site_url,
            payload.competitor_company_name,
            payload.estimated_page_count,
            payload.cms_required,
            payload.contact_form_required,
            payload.special_function_required,
            payload.seo_required,
            payload.content_creation_required,
            payload.desired_launch_timing,
            payload.budget_range,
            payload.own_service_info,
            payload.past_proposal_template,
            payload.case_studies,
        ]
    )


def extract_customer_name(payload: ProposalRequest) -> str:
    first_line = next((line.strip() for line in payload.client_company_info.splitlines() if line.strip()), "")
    if first_line and "URL" not in first_line and "担当" not in first_line:
        return first_line[:120]
    match = re.search(r"(株式会社[^\s。／/\\]+|有限会社[^\s。／/\\]+|[^\s。]+会社[^\s。]*)", payload.project_brief)
    return match.group(1)[:120] if match else "提案先企業"


def extract_contact_person(payload: ProposalRequest) -> str:
    match = re.search(r"(担当者|窓口|決裁者)[:：]\s*([^\n。]+)", payload.client_company_info + "\n" + payload.project_brief)
    return match.group(2).strip()[:80] if match else ""
