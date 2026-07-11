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
首都圏で賃貸・売買仲介を行う不動産会社が、Webサイトリニューアルを検討中。
目的は、物件問い合わせ数の増加、来店予約の獲得、地域名検索からの自然流入強化。
現行サイトは情報が古く、スマホで物件情報を探しにくい。採用ページも最低限の内容のみ。
予算感は350万〜500万円、公開希望は2026年10月末。CMSでお知らせ・実績・FAQを更新したい。
既存サイトURL：https://sample-realty.example.jp
競合は地域大手の不動産会社2社。物件検索、CTA、実績訴求、SEOコンテンツで差別化したい。
決裁者は代表取締役、窓口は営業企画部。初回提案では概算費用とスケジュールも知りたい。`;
