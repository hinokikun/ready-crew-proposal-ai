from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models import PowerPointData, WinProbability


class BeautifulAiPresentationRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=120)
    powerpoint_generation_data: PowerPointData
    win_probability: WinProbability | None = None
    project_brief: str = Field("", max_length=4000)
    client_company_info: str = Field("", max_length=3000)
    competitor_site_url: str = Field("", max_length=1000)
    competitor_company_name: str = Field("", max_length=1000)
    estimated_page_count: str = Field("", max_length=300)
    cms_required: str = Field("", max_length=300)
    contact_form_required: str = Field("", max_length=300)
    special_function_required: str = Field("", max_length=500)
    seo_required: str = Field("", max_length=300)
    content_creation_required: str = Field("", max_length=300)
    desired_launch_timing: str = Field("", max_length=300)
    budget_range: str = Field("", max_length=300)
    own_service_info: str = Field("", max_length=2000)
    past_proposal_template: str = Field("", max_length=2000)
    case_studies: str = Field("", max_length=2000)
    workspace_id: str = Field("", max_length=160)
    folder_id: str = Field("", max_length=160)
    theme_id: str = Field("", max_length=160)
    image_source: str = Field("", max_length=80)
    image_style: str = Field("", max_length=160)
    language: str = Field("ja", max_length=10)
    preserve_exact_text: bool = True
    force_new: bool = False


class BeautifulAiPresentationRecord(BaseModel):
    id: int
    project_id: str
    presentation_id: str
    title: str
    editor_url: str
    player_url: str
    status: str
    theme_id: str = ""
    provider: str = "beautiful.ai"
    error_type: str = ""
    created_at: str = ""
    updated_at: str = ""


class BeautifulAiPresentationResponse(BaseModel):
    presentation_id: str
    status: str
    title: str
    editor_url: str
    player_url: str
    created_at: str
    provider: str = "beautiful.ai"
    fallback_available: bool = True


class BeautifulAiStatusResponse(BaseModel):
    enabled: bool
    configured: bool
    mock: bool
    provider: str = "beautiful.ai"
    message: str


class BeautifulAiSafeError(BaseModel):
    error_type: str
    message: str
    fallback_available: bool = True
    request_id: str = ""
    retry_after_seconds: int | None = None


class BeautifulAiStoredListResponse(BaseModel):
    presentations: list[BeautifulAiPresentationRecord]


class BeautifulAiPayload(BaseModel):
    title: str
    language: str = "ja"
    preserveExactText: bool = True
    themeId: str = ""
    workspaceId: str = ""
    folderId: str = ""
    imageSource: str = "ai"
    imageStyle: str = "clean corporate proposal"
    slides: list[dict[str, Any]]
