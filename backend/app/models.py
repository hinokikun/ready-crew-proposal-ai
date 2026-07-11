from typing import Literal

from pydantic import BaseModel, Field


class AuthLoginRequest(BaseModel):
    email: str = Field("", description="ログインメールアドレス")
    password: str = Field(..., min_length=1, description="社内試験導入用の管理者パスワード")


class AuthResponse(BaseModel):
    authenticated: bool
    token: str = ""
    expires_in_seconds: int = 0
    message: str = ""
    user: dict | None = None


class AuthStatusResponse(BaseModel):
    authenticated: bool
    auth_configured: bool
    user: dict | None = None


class UserCreateRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8)
    role: Literal["admin", "manager", "member", "viewer"]


class UserUpdateRequest(BaseModel):
    is_active: bool | None = None
    pilot_enabled: bool | None = None
    pilot_completed: bool | None = None
    pilot_note: str = Field("", max_length=500)


class PilotEndRequest(BaseModel):
    admin_comment: str = Field("", max_length=1000)


class PilotIssueCreateRequest(BaseModel):
    category: str = Field("その他", max_length=40)
    severity: Literal["critical", "high", "medium", "low"] = "medium"
    title: str = Field(..., min_length=1, max_length=160)
    summary: str = Field("", max_length=800)
    reproduction_steps: str = Field("", max_length=1000)
    assigned_to: str = Field("", max_length=120)


class PilotIssueUpdateRequest(BaseModel):
    category: str | None = Field(None, max_length=40)
    severity: Literal["critical", "high", "medium", "low"] | None = None
    title: str | None = Field(None, max_length=160)
    summary: str | None = Field(None, max_length=800)
    reproduction_steps: str | None = Field(None, max_length=1000)
    status: Literal["reported", "investigating", "fixing", "resolved", "deferred"] | None = None
    assigned_to: str | None = Field(None, max_length=120)
    resolution_note: str | None = Field(None, max_length=1000)


class FeedbackToIssueRequest(BaseModel):
    category: str = Field("その他", max_length=40)
    severity: Literal["critical", "high", "medium", "low"] = "medium"
    title: str = Field("", max_length=160)
    assigned_to: str = Field("", max_length=120)


class PilotMaintenanceModeRequest(BaseModel):
    enabled: bool
    reason: str = Field(..., min_length=3, max_length=500)


class PilotDataRetentionRequest(BaseModel):
    action: Literal[
        "keep_summary_only",
        "anonymize_events",
        "delete_events",
        "anonymize_feedback",
        "disable_test_users",
    ]
    confirm_text: str = Field("", max_length=40)


class UsageLogCreateRequest(BaseModel):
    feature_name: str
    input_length: int = 0
    output_type: str = ""
    status: Literal["success", "failure"] = "success"
    error_type: str = ""


class FeedbackCreateRequest(BaseModel):
    rating: Literal["usable", "needs_revision", "hard_to_use"]
    comment: str = Field("", max_length=1000)
    feature_name: str = Field("提案書作成", max_length=100)


class AnalyticsEventRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=120)
    event_name: str = Field(..., min_length=1, max_length=80)
    feature_name: str = Field("", max_length=80)
    status: Literal["start", "success", "failure"] = "success"
    duration_ms: int = Field(0, ge=0, le=600000)
    error_type: str = Field("", max_length=120)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class AnalyticsErrorUpdateRequest(BaseModel):
    resolved: bool


class DailyBriefingEventRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=120)
    event_type: Literal["viewed", "priority_clicked", "item_completed"]
    project_id: int | None = Field(None, ge=1)
    item_key: str = Field("", max_length=120)


IntegrationStatus = Literal["未接続", "接続準備中", "接続済み", "エラー"]
ExternalSourceType = Literal["email", "calendar", "chat", "document"]


class IntegrationSettingUpdateRequest(BaseModel):
    status: IntegrationStatus = "未接続"
    display_name: str = Field("", max_length=80)
    enabled: bool = False
    error_message: str = Field("", max_length=300)
    allowed_roles: list[Literal["admin", "manager", "member", "viewer"]] = Field(default_factory=lambda: ["admin", "manager", "member"])
    requires_admin_approval: bool = True
    data_retention_days: int = Field(90, ge=1, le=3650)
    security_note: str = Field("", max_length=1000)


class ExternalIntakeRequest(BaseModel):
    source_provider: str = Field(..., min_length=1, max_length=40)
    source_type: ExternalSourceType
    title: str = Field("", max_length=160)
    summary: str = Field("", max_length=800)
    received_at: str = Field("", max_length=80)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class ExternalIntakeReviewRequest(BaseModel):
    status: Literal["approved", "rejected", "archived"]
    review_comment: str = Field("", max_length=800)


class IntegrationDryRunRequest(BaseModel):
    provider: Literal["gmail", "outlook", "slack", "teams", "google_calendar", "google_drive"]
    template_type: Literal["case_email", "meeting_schedule", "slack_consultation", "teams_request", "proposal_request_memo", "document_share_memo"]


class ReleaseNoteCreateRequest(BaseModel):
    version: str = Field(..., min_length=1, max_length=40)
    release_date: str = Field(..., min_length=4, max_length=20)
    title: str = Field("", max_length=120)
    improvements: str = Field("", max_length=2000)


ReleaseRecordStatus = Literal["draft", "internal_test", "released", "archived"]


class ReleaseRecordCreateRequest(BaseModel):
    version: str = Field(..., min_length=1, max_length=40)
    release_date: str = Field("", max_length=20)
    status: ReleaseRecordStatus = "draft"
    summary: str = Field("", max_length=1000)
    changes: str = Field("", max_length=3000)
    impact_scope: str = Field("", max_length=1000)
    checklist: list[str] = Field(default_factory=list, max_items=30)
    known_issues: str = Field("", max_length=1500)
    rollback_note: str = Field("", max_length=1500)


class ReleaseRecordUpdateRequest(BaseModel):
    version: str | None = Field(None, min_length=1, max_length=40)
    release_date: str | None = Field(None, max_length=20)
    status: ReleaseRecordStatus | None = None
    summary: str | None = Field(None, max_length=1000)
    changes: str | None = Field(None, max_length=3000)
    impact_scope: str | None = Field(None, max_length=1000)
    checklist: list[str] | None = Field(None, max_items=30)
    known_issues: str | None = Field(None, max_length=1500)
    rollback_note: str | None = Field(None, max_length=1500)


class ReleasePublishRequest(BaseModel):
    comment: str = Field("", max_length=500)


ProjectLifecycleStatus = Literal[
    "受付",
    "ヒアリング",
    "提案中",
    "レビュー中",
    "提出済み",
    "商談中",
    "受注",
    "失注",
    "制作中",
    "納品",
    "完了",
]


class ProjectCreateRequest(BaseModel):
    customer_name: str = Field("", max_length=160)
    project_name: str = Field("", max_length=160)
    summary: str = Field("", max_length=800)
    win_probability: int = Field(0, ge=0, le=100)
    next_action: str = Field("", max_length=500)


class ProjectStatusUpdateRequest(BaseModel):
    status: ProjectLifecycleStatus
    note: str = Field("", max_length=800)


class ProjectOutcomeRequest(BaseModel):
    outcome: Literal["won", "lost"]
    lost_reason: Literal["price", "competitor", "deadline", "proposal", "other", ""] = ""
    note: str = Field("", max_length=800)


class ProjectHandoffRequest(BaseModel):
    proposal_summary: str = Field("", max_length=800)
    cautions: str = Field("", max_length=800)
    deadline: str = Field("", max_length=120)
    owner: str = Field("", max_length=120)
    special_functions: str = Field("", max_length=500)
    cms: str = Field("", max_length=120)


class ProjectCompleteRequest(BaseModel):
    success_factors: str = Field("", max_length=800)
    improvements: str = Field("", max_length=800)
    next_learnings: str = Field("", max_length=800)


class LearningImprovementStatusRequest(BaseModel):
    status: Literal["candidate", "adopted", "rejected"]


class PromptVersionCreateRequest(BaseModel):
    prompt_name: str = Field(..., min_length=2, max_length=80)
    version: str = Field(..., min_length=1, max_length=40)
    description: str = Field("", max_length=500)
    target_agent: str = Field("", max_length=80)
    prompt_template: str = Field(..., min_length=10, max_length=4000)
    status: Literal["draft", "testing", "active", "archived"] = "draft"


class PromptVersionStatusRequest(BaseModel):
    status: Literal["draft", "testing", "active", "archived"]


class PromptRollbackRequest(BaseModel):
    prompt_name: str = Field(..., min_length=2, max_length=80)
    version: str = Field(..., min_length=1, max_length=40)


class ExperimentCreateRequest(BaseModel):
    experiment_name: str = Field(..., min_length=2, max_length=120)
    target_prompt: str = Field(..., min_length=2, max_length=80)
    control_version: str = Field(..., min_length=1, max_length=40)
    candidate_version: str = Field(..., min_length=1, max_length=40)
    traffic_ratio: int = Field(50, ge=0, le=100)
    status: Literal["draft", "testing", "active", "paused", "completed", "archived"] = "testing"
    start_at: str = Field("", max_length=40)
    end_at: str = Field("", max_length=40)


class PromptRouteRequest(BaseModel):
    prompt_name: str = Field(..., min_length=2, max_length=80)
    project_id: int | None = Field(None, ge=1)


class PromptMetricRequest(BaseModel):
    experiment_id: int | None = Field(None, ge=1)
    prompt_name: str = Field(..., min_length=2, max_length=80)
    prompt_version: str = Field(..., min_length=1, max_length=40)
    project_id: int | None = Field(None, ge=1)
    outcome: Literal["won", "lost", "pending", "unknown", ""] = ""
    review_count: int = Field(0, ge=0, le=100)
    quality_gate_passed: bool = False
    proposal_time_seconds: int = Field(0, ge=0, le=86400)
    user_rating: str = Field("", max_length=40)


class KnowledgeEntryCreateRequest(BaseModel):
    industry: str = Field("", max_length=80)
    company_size: str = Field("", max_length=80)
    project_summary: str = Field(..., min_length=5, max_length=1200)
    adopted_proposal: str = Field("", max_length=1200)
    proposal_story: str = Field("", max_length=1200)
    adoption_reason: str = Field("", max_length=800)
    lost_reason: str = Field("", max_length=800)
    result: str = Field("", max_length=800)
    owner_memo: str = Field("", max_length=1200)
    outcome: Literal["success", "lost", "unknown"] = "unknown"
    rating: int = Field(3, ge=1, le=5)
    evaluation_status: Literal["effective", "needs_improvement"] = "effective"
    tags: str = Field("", max_length=500)
    approval_status: Literal["draft", "pending_review", "approved", "rejected", "archived"] = "pending_review"
    source_type: Literal["proposal_generated", "admin_created", "imported", "feedback_based"] = "admin_created"
    source_note: str = Field("", max_length=800)


class KnowledgeEvaluationRequest(BaseModel):
    rating: int = Field(3, ge=1, le=5)
    evaluation_status: Literal["effective", "needs_improvement"] = "effective"


class KnowledgeStatusUpdateRequest(BaseModel):
    approval_status: Literal["draft", "pending_review", "approved", "rejected", "archived"]


class KnowledgeSearchRequest(BaseModel):
    project_summary: str = Field(..., min_length=5, max_length=2000)
    industry: str = Field("", max_length=80)
    limit: int = Field(5, ge=1, le=10)


class ProposalTemplateCreateRequest(BaseModel):
    category: Literal["web", "recruiting", "lp", "seo", "dx", "other"] = "other"
    title: str = Field(..., min_length=1, max_length=120)
    template_summary: str = Field("", max_length=800)
    structure: str = Field("", max_length=2000)
    recommended_for: str = Field("", max_length=800)
    is_active: bool = True


class ProposalTemplateUpdateRequest(BaseModel):
    is_active: bool


class TrialReportRequest(BaseModel):
    admin_comment: str = Field("", max_length=2000)


class WorkspaceConversationInput(BaseModel):
    client_message_id: str = Field(..., min_length=1, max_length=120)
    agent_name: str = Field(..., min_length=1, max_length=40)
    message_type: str = Field("normal", max_length=40)
    message_body: str = Field("", max_length=500)
    status: str = Field("active", max_length=40)


class WorkspaceWorkLogInput(BaseModel):
    client_log_id: str = Field(..., min_length=1, max_length=120)
    agent_name: str = Field(..., min_length=1, max_length=40)
    action_summary: str = Field("", max_length=500)
    status: str = Field("active", max_length=40)


class WorkspaceConversationSaveRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=120)
    conversations: list[WorkspaceConversationInput] = Field(default_factory=list, max_items=80)
    work_logs: list[WorkspaceWorkLogInput] = Field(default_factory=list, max_items=80)


class ProposalReviewRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=120)
    project_name: str = Field("", max_length=160)


class ProposalReviewUpdateRequest(BaseModel):
    status: Literal["approved", "changes_requested", "rejected"]
    review_comment: str = Field("", max_length=1000)


class ProposalReviewRecreateRequest(BaseModel):
    current_summary: str = Field("", max_length=800)


class QualityGateSaveRequest(BaseModel):
    checklist_items: list[str] = Field(default_factory=list, max_items=20)


class QualityGateCompleteRequest(BaseModel):
    checklist_items: list[str] = Field(default_factory=list, max_items=20)


class QualityGateBypassRequest(BaseModel):
    bypass_reason: str = Field(..., min_length=3, max_length=500)


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
    knowledge_insights: dict = Field(default_factory=dict)


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

