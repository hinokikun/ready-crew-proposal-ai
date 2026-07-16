import type { FeedbackRating, FeedbackSummary } from "@/lib/api";
import type { ProposalRequest } from "@/types/proposal";

export const HISTORY_KEY = "ready-crew-proposal-history-v1";
export const GUIDE_TUTORIAL_KEY = "ready-crew-guide-tutorial-seen-v1";
export const PILOT_CHECKLIST_KEY = "ai-sales-secretary-pilot-checklist-v1";
export const MAX_HISTORY_COUNT = 10;

export const emptyFeedbackSummary: FeedbackSummary = {
  usable: 0,
  needs_revision: 0,
  hard_to_use: 0,
  comments: 0
};

export const feedbackRatingLabels: Record<FeedbackRating, string> = {
  usable: "使えそう",
  needs_revision: "修正すれば使えそう",
  hard_to_use: "使いにくい"
};

export const pilotFeedbackQuestions = [
  { key: "easy_to_use", label: "迷わず使えた" },
  { key: "output_quality", label: "提案書の品質に納得できた" },
  { key: "time_saved", label: "作成時間を短縮できた" },
  { key: "safe_to_use", label: "安心して使えた" },
  { key: "continue_using", label: "今後も使いたい" }
] as const;

export type PilotFeedbackKey = (typeof pilotFeedbackQuestions)[number]["key"];
export type PilotFeedbackScores = Record<PilotFeedbackKey, number>;

export const initialPilotFeedbackScores: PilotFeedbackScores = {
  easy_to_use: 0,
  output_quality: 0,
  time_saved: 0,
  safe_to_use: 0,
  continue_using: 0
};

export const initialForm: ProposalRequest = {
  project_brief: "",
  client_company_info: "",
  competitor_site_url: "",
  competitor_company_name: "",
  estimated_page_count: "",
  cms_required: "",
  contact_form_required: "",
  special_function_required: "",
  seo_required: "",
  content_creation_required: "",
  desired_launch_timing: "",
  budget_range: "",
  hearing_result: "",
  own_service_info: "",
  past_proposal_template: "",
  case_studies: ""
};

export const sampleBrief = `Ready Crew案件概要：
経理部門が、請求書のAI-OCR読み取りと会計システム連携を検討中。
目的は、手入力時間の削減、入力ミスの抑制、月次処理の標準化。
現状はPDF請求書を人が確認し、会社名、日付、金額、請求書番号をExcelへ転記している。
予算感は300万〜500万円、PoCは2〜3か月で実施したい。
連携先はCSVまたは会計システムAPI。読取精度、例外確認フロー、運用支援も確認したい。
比較対象はAI-OCRクラウドサービス。初回提案では概算費用とスケジュールも知りたい。`;
