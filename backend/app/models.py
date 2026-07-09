from typing import Literal

from pydantic import BaseModel, Field


class AuthLoginRequest(BaseModel):
    password: str = Field(..., min_length=1, description="社内試験導入用の管理者パスワード")


class AuthResponse(BaseModel):
    authenticated: bool
    token: str = ""
    expires_in_seconds: int = 0
    message: str = ""


class AuthStatusResponse(BaseModel):
    authenticated: bool
    auth_configured: bool


class ProposalRequest(BaseModel):
    project_brief: str = Field(..., min_length=20, description="Ready Crew の案件概要テキスト")
    client_company_info: str = Field("", description="提案先企業情報")
    competitor_site_url: str = Field("", description="競合サイトURL")
    competitor_company_name: str = Field("", description="競合企業名")
    estimated_page_count: str = Field("", description="想定ページ数")
    cms_required: str = Field("", description="CMS有無")
    contact_form_required: str = Field("", description="問い合わせフォーム有無")
    special_function_required: str = Field("", description="物件検索などの特殊機能有無")
    seo_required: str = Field("", description="SEO対策有無")
    content_creation_required: str = Field("", description="撮影・原稿作成有無")
    desired_launch_timing: str = Field("", description="公開希望時期")
    budget_range: str = Field("", description="予算感")
    hearing_result: str = Field("", description="ヒアリング結果")
    own_service_info: str = Field("", description="自社サービス情報")
    past_proposal_template: str = Field("", description="過去提案書テンプレート")
    case_studies: str = Field("", description="成功事例データ")


class CompanyResearchRequest(BaseModel):
    url: str = Field("", description="調査対象の会社URL")
    project_brief: str = Field("", description="案件概要")
    client_company_info: str = Field("", description="提案先企業情報")


class CompanyResearchResponse(BaseModel):
    source_url: str
    fetched: bool
    overview: str
    competitors: list[str]
    recruitment: str
    news: list[str]
    services: list[str]
    sns: list[str]


class AssumedIssue(BaseModel):
    issue: str
    background: str
    evidence: str
    confidence: str


class IssuePriority(BaseModel):
    rank: int
    issue: str
    reason: str
    proposed_response: str


class WinProbability(BaseModel):
    rank: Literal["A", "B", "C", "D"]
    probability: int = Field(0, description="受注確率（%）")
    label: str
    reason: str
    risk_score: int = Field(3, ge=1, le=5, description="受注リスク。1が低リスク、5が高リスク")
    risk_label: str = Field("", description="受注リスクの星表示")
    positive_factors: list[str]
    risk_factors: list[str]
    recommended_next_actions: list[str]
    improvement_actions: list[str] = Field(default_factory=list, description="受注確率を上げる改善アクション")
    projected_probability_after_actions: int = Field(0, description="改善アクション実施後の受注確率予測（%）")


class ProposalStructureItem(BaseModel):
    section: str
    objective: str
    key_message: str


class SlideScript(BaseModel):
    slide_no: int
    section: str
    title: str
    body: list[str]
    speaker_notes: str
    visual_suggestion: str


class ExpectedQuestion(BaseModel):
    question: str
    answer: str


class QualityCheck(BaseModel):
    logical_consistency: str
    typos: str
    proposal_coverage: str
    competitive_differentiation: str
    alignment_with_customer_issues: str
    human_review_notes: str


class PowerPointSlide(BaseModel):
    slide_no: int
    layout: str
    title: str
    bullets: list[str]
    speaker_notes: str
    visual_suggestion: str


class PowerPointData(BaseModel):
    deck_title: str
    client_name: str
    slides: list[PowerPointSlide]


class ProposalAnalysis(BaseModel):
    project_summary: str
    assumed_customer_issues: list[AssumedIssue]
    issue_priorities: list[IssuePriority]
    win_probability: WinProbability
    proposal_policy: str
    proposal_story: str
    proposal_structure: list[ProposalStructureItem]
    slide_scripts: list[SlideScript]
    expected_questions_and_answers: list[ExpectedQuestion]
    quality_check: QualityCheck
    powerpoint_generation_data: PowerPointData


class AnalysisResponse(BaseModel):
    analysis: ProposalAnalysis
    markdown: str
    powerpoint_generation_data: PowerPointData


class PptxDownloadRequest(BaseModel):
    powerpoint_generation_data: PowerPointData
    win_probability: WinProbability | None = None
    project_brief: str = Field("", description="Ready Crew の案件概要テキスト")
    client_company_info: str = Field("", description="提案先企業情報")
    competitor_site_url: str = Field("", description="競合サイトURL")
    competitor_company_name: str = Field("", description="競合企業名")
    estimated_page_count: str = Field("", description="想定ページ数")
    cms_required: str = Field("", description="CMS有無")
    contact_form_required: str = Field("", description="問い合わせフォーム有無")
    special_function_required: str = Field("", description="物件検索などの特殊機能有無")
    seo_required: str = Field("", description="SEO対策有無")
    content_creation_required: str = Field("", description="撮影・原稿作成有無")
    desired_launch_timing: str = Field("", description="公開希望時期")
    budget_range: str = Field("", description="予算感")
    hearing_result: str = Field("", description="ヒアリング結果")
    own_service_info: str = Field("", description="自社サービス情報")
    past_proposal_template: str = Field("", description="過去提案書テンプレート")
    case_studies: str = Field("", description="成功事例データ")
    summary: bool = Field(False, description="要約版PowerPointとして生成するか")

