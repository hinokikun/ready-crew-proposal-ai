export type UserRole = "admin" | "manager" | "member" | "viewer";

export type AuthUser = {
  id: number;
  email: string;
  role: UserRole;
  is_active?: boolean;
  pilot_enabled?: boolean;
  pilot_started_at?: string;
  pilot_last_used_at?: string;
  pilot_completed?: boolean;
  pilot_note?: string;
};

export type LoginResult = {
  authenticated: boolean;
  token: string;
  expires_in_seconds: number;
  message: string;
  user?: AuthUser;
};

export type ManagedUser = {
  id: number;
  email: string;
  role: UserRole;
  is_active: number | boolean;
  pilot_enabled?: number | boolean;
  pilot_started_at?: string;
  pilot_last_used_at?: string;
  pilot_completed?: number | boolean;
  pilot_note?: string;
  created_at: string;
  updated_at: string;
};

export type PilotStatus = {
  pilot_mode: boolean;
  maintenance_mode: boolean;
  pilot_start_date: string;
  pilot_end_date: string;
  pilot_max_users: number;
  days_remaining: number | null;
  notice: string;
};

export type PilotDashboardData = {
  status: PilotStatus;
  summary: {
    enabled_users: number;
    started_users: number;
    active_this_week: number;
    usage_rate?: number;
    proposal_count: number;
    proposal_generations: number;
    downloads: number;
    success_rate: number;
    error_count: number;
    feedback_count: number;
    feedback_average?: number;
    critical_issue_count?: number;
    unresolved_issue_count?: number;
    issue_count?: number;
    average_processing_ms?: number;
    unused_users: number;
    max_users: number;
    days_remaining: number | null;
    days_to_end: number | null;
  };
  users: Array<{
    id: number;
    email: string;
    role: UserRole | string;
    pilot_enabled: number | boolean;
    pilot_started_at: string | null;
    pilot_last_used_at: string | null;
    pilot_completed: number | boolean;
    pilot_note: string;
    usage_count: number;
    success_count: number;
    failure_count: number;
  }>;
  unused_users: Array<{ id: number; email: string; role: UserRole | string; pilot_note: string }>;
  success_criteria: Array<{ key?: string; label: string; value: number; target: number; met: boolean; unit?: string }>;
  feedback_metrics?: PilotFeedbackMetrics;
  issues?: PilotIssue[];
  incidents?: PilotIncident[];
  judgment?: PilotJudgment;
  maintenance?: PilotMaintenanceState;
  recent_feedback?: PilotFeedbackPreview[];
  retention_preview?: PilotRetentionPreview;
};

export type PilotIssueSeverity = "critical" | "high" | "medium" | "low";
export type PilotIssueStatus = "reported" | "investigating" | "fixing" | "resolved" | "deferred";

export type PilotIssue = {
  id: number;
  issue_id: string;
  category: string;
  severity: PilotIssueSeverity | string;
  title: string;
  summary: string;
  reproduction_steps: string;
  status: PilotIssueStatus | string;
  reported_by: number | null;
  reported_by_email?: string | null;
  assigned_to: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  resolution_note: string;
  source_feedback_id?: number | null;
};

export type PilotFeedbackMetrics = {
  average_usability: number;
  practical_usability_rate: number;
  time_saved_rate: number;
  continue_intent_rate: number;
  score_count: number;
};

export type PilotIncident = {
  key: string;
  severity: string;
  title: string;
  detail: string;
};

export type PilotJudgment = {
  result: string;
  criteria: Array<{ key: string; label: string; value: number; target: number; met: boolean; unit: string }>;
  reasons: string[];
  feedback_metrics: PilotFeedbackMetrics;
};

export type PilotMaintenanceState = {
  env_enabled: boolean;
  runtime_enabled: boolean;
  effective: boolean;
  reason: string;
  updated_at: string;
  updated_by: number | null;
};

export type PilotFeedbackPreview = {
  id: number;
  rating: FeedbackRating | string;
  comment_summary: string;
  feature_name: string;
  user_role: string;
  created_at: string;
};

export type PilotRetentionPreview = {
  pilot_events: number;
  pilot_feedback: number;
  pilot_users: number;
  pilot_issues: number;
  production_projects: number;
  knowledge_entries: number;
  audit_logs: number;
};

export type PilotEndReport = {
  dashboard: PilotDashboardData;
  feedback_summary: FeedbackSummary;
  next_improvements: string[];
  issues?: PilotIssue[];
  resolved_issues?: PilotIssue[];
  unresolved_issues?: PilotIssue[];
  judgment?: PilotJudgment;
  markdown: string;
};

export type CrmCustomer = {
  id: number;
  company_name: string;
  industry: string;
  contact_person: string;
  updated_at: string;
};

export type CrmProject = {
  id: number;
  name: string;
  customer_name?: string;
  status: string;
  review_status?: string;
  outcome?: string;
  lost_reason?: string;
  win_probability: number;
  summary: string;
  next_action: string;
  updated_at: string;
};

export type ProjectLifecycleStatus =
  | "受付"
  | "ヒアリング"
  | "提案中"
  | "レビュー中"
  | "提出済み"
  | "商談中"
  | "受注"
  | "失注"
  | "制作中"
  | "納品"
  | "完了";

export type ProjectLifecycleEvent = {
  id: number;
  project_id: number;
  user_id: number | null;
  user_email?: string;
  event_type: string;
  from_status: string;
  to_status: string;
  note: string;
  created_at: string;
};

export type ProjectOutcome = {
  id: number;
  project_id: number;
  outcome: "won" | "lost" | string;
  lost_reason: string;
  note: string;
  created_at: string;
  updated_at: string;
};

export type ProjectHandoff = {
  id: number;
  project_id: number;
  handoff_text: string;
  created_at: string;
  updated_at: string;
};

export type ProjectRetrospective = {
  id: number;
  project_id: number;
  success_factors: string;
  improvements: string;
  next_learnings: string;
  knowledge_candidate_id: number | null;
  created_at: string;
  updated_at: string;
};

export type ProjectLifecycleDetail = {
  project: CrmProject & {
    proposal_histories?: unknown[];
    meeting_memos?: unknown[];
    workspace_conversations?: unknown[];
    workspace_work_logs?: unknown[];
    proposal_reviews?: ProposalReviewEntry[];
  };
  statuses: ProjectLifecycleStatus[];
  timeline: ProjectLifecycleEvent[];
  outcome: ProjectOutcome | null;
  handoff: ProjectHandoff | null;
  retrospective: ProjectRetrospective | null;
};

export type ProjectLostReason = "price" | "competitor" | "deadline" | "proposal" | "other" | "";

export type ProjectLifecycleAnalytics = {
  total_projects: number;
  won_count: number;
  lost_count: number;
  win_rate: number;
  average_proposal_days: number;
  review_count: number;
  revision_count: number;
  lost_reasons: Array<{ reason: string; label: string; count: number }>;
  completed_count: number;
  completion_rate: number;
};

export type AuditLog = {
  id: number;
  user_id: number | null;
  user_email?: string | null;
  event_type: string;
  target_type: string;
  target_id: string;
  status: "success" | "failure" | string;
  metadata: string;
  created_at: string;
};

export type FeedbackRating = "usable" | "needs_revision" | "hard_to_use";

export type FeedbackEntry = {
  id: number;
  user_id: number | null;
  user_email?: string | null;
  user_role: UserRole | string;
  rating: FeedbackRating;
  comment: string;
  feature_name: string;
  created_at: string;
};

export type FeedbackSummary = {
  usable: number;
  needs_revision: number;
  hard_to_use: number;
  comments: number;
};

export type UsageDashboardSummary = {
  total_usage: number;
  today_usage: number;
  week_usage: number;
  proposal_generation: number;
  ppt_download: number;
  error_count: number;
  feedback_count: number;
};

export type UsageErrorAnalysis = {
  api_limit: number;
  backend_unreachable: number;
  input_missing: number;
  ppt_generation_failed: number;
  auth_error: number;
};

export type UsageByUser = {
  user_id: number | null;
  user_name: string;
  user_role: UserRole | string;
  usage_count: number;
  last_used_at: string;
  success_count: number;
  failure_count: number;
};

export type UsageByFeature = {
  feature_key: string;
  feature_name: string;
  usage_count: number;
  success_count: number;
  failure_count: number;
};

export type UsageDashboardData = {
  summary: UsageDashboardSummary;
  error_analysis: UsageErrorAnalysis;
  users: UsageByUser[];
  features: UsageByFeature[];
  feedback_summary: FeedbackSummary;
};

export type TrialReportData = {
  period: {
    start: string;
    end: string;
    label: string;
  };
  summary_text: string;
  numeric_summary: UsageDashboardSummary;
  feedback_summary: FeedbackSummary;
  error_analysis: UsageErrorAnalysis;
  good_points: string[];
  issues: string[];
  next_actions: string[];
  rollout_opinion: string;
  admin_comment: string;
  markdown: string;
};

export type OperationReadinessStatus = "ok" | "warning" | "missing";

export type OperationReadinessItem = {
  key: string;
  label: string;
  status: OperationReadinessStatus;
  detail: string;
  next_action: string;
};

export type OperationReadinessData = {
  generated_at: string;
  score: number;
  score_label: string;
  checks: OperationReadinessItem[];
  security_checks: OperationReadinessItem[];
  next_actions: string[];
  markdown: string;
};

export type ImprovementPriority = "高" | "中" | "低";

export type ImprovementCategory = "UI/UX" | "AI精度" | "運用" | "セキュリティ" | "パフォーマンス" | "連携" | string;

export type ImprovementSuggestion = {
  priority: ImprovementPriority | string;
  category: ImprovementCategory;
  title: string;
  reason: string;
  expected_effect: string;
  difficulty: string;
  next_step: string;
};

export type ImprovementDashboardData = {
  summary: {
    total_usage: number;
    error_count: number;
    feedback_count: number;
    hard_to_use: number;
    readiness_score: number;
  };
  improvements: ImprovementSuggestion[];
  roadmap: {
    now: string[];
    this_month: string[];
    future: string[];
  };
  executive_summary: string;
  markdown: string;
};

export type AnalyticsEventStatus = "start" | "success" | "failure";

export type ProductAnalyticsEventPayload = {
  session_id: string;
  event_name: string;
  feature_name?: string;
  status?: AnalyticsEventStatus;
  duration_ms?: number;
  error_type?: string;
  metadata?: Record<string, string | number | boolean | null | undefined>;
};

export type FunnelStepData = {
  step: string;
  label: string;
  sessions: number;
  reach_rate: number;
  dropoff_rate: number;
  average_time_seconds: number;
};

export type AnalyticsSession = {
  id: number;
  session_key: string;
  user_id: number | null;
  user_name: string;
  user_role: UserRole | string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number;
  generation_count: number;
  download_count: number;
  error_count: number;
};

export type AnalyticsErrorItem = {
  id: number;
  category: string;
  message: string;
  source: string;
  count: number;
  percentage: number;
  first_seen_at: string;
  last_seen_at: string;
  resolved: boolean;
};

export type FeatureUsageItem = {
  feature_key: string;
  feature_name: string;
  event_count: number;
  session_count: number;
  usage_rate: number;
};

export type ProductAnalyticsImprovement = {
  priority: string;
  title: string;
  reason: string;
  hypothesis: string;
  next_action: string;
};

export type ActionQueueStatus = "pending" | "running" | "success" | "failure" | "retry_waiting" | "needs_human" | string;

export type ActionQueueItem = {
  id: number;
  project_id: number | null;
  project_name: string;
  customer_name: string;
  action_type: string;
  action_label: string;
  agent: string;
  next_agent: string;
  status: ActionQueueStatus;
  priority: number;
  reason: string;
  result_summary: string;
  error_type: string;
  created_by: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  retry_count: number;
};

export type OrchestratorStatus = {
  project_id: number;
  current_action: ActionQueueItem | null;
  next_action: ActionQueueItem | null;
  counts: Record<string, number>;
  queue: ActionQueueItem[];
};

export type OrchestratorAnalytics = {
  total_actions: number;
  average_processing_seconds: number;
  retry_rate: number;
  autonomous_completion_rate: number;
  human_intervention_rate: number;
  status_counts: Record<string, number>;
  agent_times: Array<{
    agent: string;
    total_seconds: number;
    average_seconds: number;
    action_count: number;
  }>;
};

export type LearningSimulation = {
  win_rate_delta?: number;
  review_count_delta?: number;
  quality_gate_pass_delta?: number;
  proposal_time_delta?: number;
};

export type LearningImprovement = {
  id: number;
  run_id: number | null;
  improvement_type: "prompt" | "workflow" | "rule" | string;
  agent: string;
  category: string;
  current_version: string;
  suggested_prompt: string;
  recommendation: string;
  expected_effect: string;
  confidence: number;
  priority: number;
  simulation: LearningSimulation;
  status: "candidate" | "adopted" | "rejected" | string;
  created_at: string;
  updated_at: string;
  release_candidate_version?: string;
};

export type LearningRun = {
  id: number;
  triggered_by: number | null;
  status: string;
  analyzed_items_count: number;
  metrics_summary: Record<string, unknown>;
  release_candidate_version: string;
  release_candidate_summary: string;
  created_at: string;
};

export type LearningAnalytics = {
  learning_runs: number;
  improvement_adoption_rate: number;
  average_expected_win_rate_delta: number;
  prompt_improvements: number;
  workflow_improvements: number;
  total_improvements: number;
};

export type LearningDashboardData = {
  run: LearningRun | null;
  improvements: LearningImprovement[];
  release_candidate: {
    version: string;
    summary: string;
  };
  analytics: LearningAnalytics;
};

export type PromptVersionStatus = "draft" | "testing" | "active" | "archived" | string;

export type PromptVersion = {
  id: number;
  prompt_name: string;
  version: string;
  description: string;
  target_agent: string;
  prompt_template: string;
  created_by: number | null;
  created_by_email?: string;
  created_at: string;
  status: PromptVersionStatus;
};

export type PromptExperiment = {
  id: number;
  experiment_name: string;
  target_prompt: string;
  control_version: string;
  candidate_version: string;
  traffic_ratio: number;
  status: string;
  start_at: string;
  end_at: string;
  winner: string;
  created_by: number | null;
  created_by_email?: string;
  created_at: string;
  updated_at: string;
};

export type PromptMetricSummary = {
  prompt_name: string;
  prompt_version: string;
  sample_count: number;
  won_count: number;
  lost_count: number;
  review_count: number;
  quality_gate_passed_count: number;
  average_proposal_time_seconds: number;
  win_rate: number;
  quality_gate_pass_rate: number;
};

export type PromptWinnerRecommendation = {
  experiment_id: number;
  experiment_name: string;
  target_prompt: string;
  recommended_version: string;
  reason: string;
  confidence: number;
};

export type PromptExperimentAnalytics = {
  prompt_versions_count: number;
  experiments_count: number;
  active_experiments_count: number;
  assignments_count: number;
  metrics_count: number;
  prompt_metrics: PromptMetricSummary[];
  winner_recommendations: PromptWinnerRecommendation[];
};

export type PromptStudioDashboardData = {
  versions: PromptVersion[];
  experiments: PromptExperiment[];
  analytics: PromptExperimentAnalytics;
  winner_recommendations: PromptWinnerRecommendation[];
};

export type ProductAnalyticsDashboardData = {
  summary: {
    total_sessions: number;
    total_events: number;
    total_errors: number;
    average_session_seconds: number;
  };
  funnel: FunnelStepData[];
  sessions: AnalyticsSession[];
  errors: AnalyticsErrorItem[];
  feature_usage: FeatureUsageItem[];
  improvement_candidates: ProductAnalyticsImprovement[];
  project_lifecycle?: ProjectLifecycleAnalytics;
  daily_briefing?: DailyBriefingAnalytics;
  notification_center?: AiNotificationAnalytics;
  integrations?: IntegrationAnalytics;
  orchestrator?: OrchestratorAnalytics;
  learning?: LearningAnalytics;
  prompt_experiments?: PromptExperimentAnalytics;
};

export type IntegrationStatus = "未接続" | "接続準備中" | "接続済み" | "エラー" | string;

export type IntegrationSetting = {
  id: number;
  provider: string;
  status: IntegrationStatus;
  display_name: string;
  enabled: boolean;
  allowed_roles: UserRole[];
  requires_admin_approval: boolean;
  data_retention_days: number;
  last_checked_at: string | null;
  last_security_review_at: string | null;
  error_message: string;
  security_note: string;
  created_at: string;
  updated_at: string;
};

export type ExternalIntakeSourceType = "email" | "calendar" | "chat" | "document";

export type ExternalIntakeCandidate = {
  id: number;
  source_provider: string;
  source_type: ExternalIntakeSourceType | string;
  title: string;
  summary: string;
  received_at: string;
  metadata: Record<string, string | number | boolean | null>;
  candidate_status: "received" | "pending_review" | "approved" | "rejected" | "converted" | "archived" | string;
  security_flags: Array<{ type: string; field: string; severity: string }>;
  reviewed_by: number | null;
  reviewed_at: string | null;
  review_comment: string;
  created_by: number | null;
  created_by_email?: string;
  project_id: number | null;
  project_name?: string;
  created_at: string;
  updated_at: string;
};

export type IntegrationDryRunTemplate =
  | "case_email"
  | "meeting_schedule"
  | "slack_consultation"
  | "teams_request"
  | "proposal_request_memo"
  | "document_share_memo";

export type IntegrationDryRunResult = {
  provider: string;
  template_type: IntegrationDryRunTemplate | string;
  status: "success" | "failure" | string;
  created_item_id: number | null;
  result_summary: string;
  security_flags_count: number;
  checks: {
    registered: boolean;
    security_scanned: boolean;
    pending_review: boolean;
    can_convert_after_approval: boolean;
    workspace_handoff_after_conversion: boolean;
  };
};

export type DryRunLog = {
  id: number;
  provider: string;
  template_type: string;
  status: string;
  created_item_id: number | null;
  result_summary: string;
  security_flags_count: number;
  created_by: number | null;
  created_by_email?: string;
  created_at: string;
};

export type ConnectorReadinessItem = {
  provider: string;
  display_name: string;
  score: number;
  status: "ready" | "needs_review" | string;
  checks: Record<string, boolean>;
  last_dry_run_at: string;
};

export type IntegrationAnalytics = {
  external_input_count: number;
  candidate_count: number;
  converted_count: number;
  conversion_rate: number;
  provider_counts: Array<{ provider: string; count: number }>;
  dry_run_count?: number;
  provider_dry_run_success_rates?: Array<{ provider: string; total: number; success_count: number; success_rate: number }>;
  average_readiness_score?: number;
};

export type AiNotificationPriority = "高" | "中" | "低" | string;

export type AiNotificationStatus = "unread" | "read" | "archived" | string;

export type AiNotification = {
  id: number;
  notification_key: string;
  user_id: number | null;
  project_id: number | null;
  project_name?: string | null;
  customer_name?: string | null;
  agent_name: string;
  priority: AiNotificationPriority;
  title: string;
  message: string;
  recommended_action: string;
  source_type: string;
  source_id: string;
  status: AiNotificationStatus;
  created_at: string;
  updated_at: string;
  read_at: string | null;
  archived_at: string | null;
  actioned_at: string | null;
};

export type AiNotificationSummary = {
  total: number;
  unread: number;
  high: number;
  medium: number;
  low: number;
};

export type AiNotificationCenterData = {
  notifications: AiNotification[];
  summary: AiNotificationSummary;
};

export type AiNotificationAnalytics = {
  total: number;
  unread: number;
  read_rate: number;
  action_rate: number;
  ignored_rate: number;
};

export type DailyBriefingSummary = {
  action_required_count: number;
  review_waiting: number;
  changes_requested: number;
  due_soon: number;
  expected_wins: number;
  stagnant: number;
};

export type DailyBriefingSuggestion = {
  key: string;
  project_id: number;
  title: string;
  priority: "高" | "中" | "低" | string;
  reason: string;
  recommended_action: string;
  deadline: string;
  review_status: string;
  win_probability: number;
};

export type DailyBriefingTimelineItem = {
  time: string;
  label: string;
  description: string;
};

export type DailyBriefingAgentComment = {
  agent: string;
  comment: string;
};

export type DailyBriefingData = {
  generated_at: string;
  summary: DailyBriefingSummary;
  suggestions: DailyBriefingSuggestion[];
  timeline: DailyBriefingTimelineItem[];
  recommended_project: DailyBriefingSuggestion | null;
  agent_comments: DailyBriefingAgentComment[];
};

export type DailyBriefingAnalytics = {
  views: number;
  priority_clicks: number;
  completed: number;
  completion_rate: number;
};

export type ReleaseNoteEntry = {
  id: number;
  version: string;
  release_date: string;
  title: string;
  improvements: string;
  created_by: number | null;
  created_by_email: string;
  created_at: string;
};

export type ReleaseRecordStatus = "draft" | "internal_test" | "released" | "archived";

export type ReleaseRecord = {
  id: number;
  version: string;
  release_date: string;
  status: ReleaseRecordStatus | string;
  summary: string;
  changes: string;
  impact_scope: string;
  checklist: string[];
  known_issues: string;
  rollback_note: string;
  created_by: number | null;
  created_by_email?: string;
  released_by: number | null;
  released_by_email?: string;
  released_at: string | null;
  created_at: string;
  updated_at: string;
};

export type KnowledgeOutcome = "success" | "lost" | "unknown";
export type KnowledgeEvaluationStatus = "effective" | "needs_improvement";
export type KnowledgeApprovalStatus = "draft" | "pending_review" | "approved" | "rejected" | "archived";
export type KnowledgeSourceType = "proposal_generated" | "admin_created" | "imported" | "feedback_based";
export type ProposalTemplateCategory = "web" | "recruiting" | "lp" | "seo" | "dx" | "other";

export type ProposalKnowledgeEntry = {
  id: number;
  industry: string;
  company_size: string;
  project_summary: string;
  adopted_proposal: string;
  proposal_story: string;
  adoption_reason: string;
  lost_reason: string;
  result: string;
  owner_memo: string;
  outcome: KnowledgeOutcome | string;
  rating: number;
  evaluation_status: KnowledgeEvaluationStatus | string;
  tags: string;
  approval_status: KnowledgeApprovalStatus | string;
  quality_score: number;
  confidential_risk: "low" | "medium" | "high" | string;
  confidential_flags: string;
  confidential_flags_list?: string[];
  source_type: KnowledgeSourceType | string;
  source_note: string;
  is_high_quality?: boolean;
  similarity_score?: number;
  created_at: string;
  updated_at: string;
  created_by_email?: string;
};

export type KnowledgeBestPractices = {
  winning_structures: string[];
  frequent_proposals: string[];
  industry_success_examples: Array<{ industry: string; count: number }>;
};

export type KnowledgeSearchInsights = {
  industry: string;
  matches: ProposalKnowledgeEntry[];
  success_patterns: string[];
  lost_patterns: string[];
  recommendation: string;
};

export type ProposalTemplateEntry = {
  id: number;
  category: ProposalTemplateCategory | string;
  title: string;
  template_summary: string;
  structure: string;
  recommended_for: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by_email?: string;
};

export type WorkspaceConversationRecord = {
  id: number;
  project_id: string;
  user_id: number | null;
  user_email?: string | null;
  client_message_id: string;
  agent_name: string;
  message_type: string;
  message_body: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type WorkspaceWorkLogRecord = {
  id: number;
  project_id: string;
  user_id: number | null;
  user_email?: string | null;
  client_log_id: string;
  agent_name: string;
  action_summary: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type WorkspaceSummary = {
  project_id: string;
  reception: string;
  proposal_policy: string;
  review: string;
  schedule_check: string;
  final_decision: string;
  next_action: string;
  latest_log?: string;
  log_count: number;
  conversation_count: number;
  markdown: string;
};

export type ProposalReviewStatus = "draft" | "review_requested" | "approved" | "changes_requested" | "rejected";

export type ProposalReviewEntry = {
  id: number;
  project_id: string;
  project_name: string;
  creator_user_id: number | null;
  creator_email?: string | null;
  status: ProposalReviewStatus | string;
  review_comment: string;
  reviewer_user_id: number | null;
  reviewer_email?: string | null;
  review_requested_at: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ProposalReviewRevision = {
  id: number;
  review_id: number;
  project_id: string;
  previous_status: string;
  next_status: string;
  review_comment: string;
  ai_improvement_policy: string;
  diff_summary: string;
  executed_by_user_id: number | null;
  executed_by_email?: string | null;
  created_at: string;
};

export type QualityGateRecord = {
  id: number;
  project_id: string;
  user_id: number | null;
  checklist_items: string[];
  completed: boolean;
  completed_at: string | null;
  bypassed: boolean;
  bypass_reason: string;
  created_at: string;
  updated_at: string;
  download_unlocked: boolean;
};
