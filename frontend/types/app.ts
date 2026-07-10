export type UserRole = "admin" | "member" | "viewer";

export type AuthUser = {
  id: number;
  email: string;
  role: UserRole;
  is_active?: boolean;
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
  created_at: string;
  updated_at: string;
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
  win_probability: number;
  summary: string;
  next_action: string;
  updated_at: string;
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
