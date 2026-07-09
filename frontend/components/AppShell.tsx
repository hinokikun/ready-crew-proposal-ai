"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  Clipboard,
  Download,
  Mail,
  FileDown,
  FileCheck2,
  FileText,
  History,
  Loader2,
  Mic,
  MessageCircle,
  RotateCcw,
  Send,
  Sparkles,
  UploadCloud,
  X
} from "lucide-react";
import { AuthGate } from "@/components/AuthGate";
import { AdminAuditLogPanel } from "@/components/AdminAuditLogPanel";
import { AdminUsersPanel } from "@/components/AdminUsersPanel";
import { CrmPanel } from "@/components/CrmPanel";
import { Dashboard } from "@/components/Dashboard";
import { Header } from "@/components/Header";
import { HealthStatus, type HealthSnapshot } from "@/components/HealthStatus";
import { PermissionNotice } from "@/components/PermissionNotice";
import { SecurityNotice } from "@/components/SecurityNotice";
import { SettingsPanel } from "@/components/SettingsPanel";
import { StatusMessage } from "@/components/ui/StatusMessage";
import {
  analyzeProposal,
  createUser,
  getAuditLogs,
  getCrm,
  getDbLogs,
  listUsers,
  researchCompanyUrl,
  saveUsageLogToBackend,
  updateUserActive,
  type CrmCustomer,
  type CrmProject,
  type ManagedUser,
  type AuditLog
} from "@/lib/api";
import { getStoredUser, type AuthUser } from "@/lib/auth";
import { toFriendlyError } from "@/lib/errorMessage";
import { downloadEstimatePdf } from "@/lib/pdf";
import { downloadProposalPowerPoint, downloadSummaryProposalPowerPoint } from "@/lib/pptx";
import { appendUsageLog, readUsageLogs, type UsageLogEntry } from "@/lib/storage";
import type { AnalysisResponse, ProposalRequest, WinProbability } from "@/types/proposal";

const HISTORY_KEY = "ready-crew-proposal-history-v1";
const MAX_HISTORY_COUNT = 10;

const initialForm: ProposalRequest = {
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

const sampleBrief = `Ready Crew案件概要：
首都圏で賃貸・売買仲介を行う不動産会社が、Webサイトリニューアルを検討中。
目的は、物件問い合わせ数の増加、来店予約の獲得、地域名検索からの自然流入強化。
現行サイトは情報が古く、スマホで物件情報を探しにくい。採用ページも最低限の内容のみ。
予算感は350万〜500万円、公開希望は2026年10月末。CMSでお知らせ・実績・FAQを更新したい。
既存サイトURL：https://sample-realty.example.jp
競合は地域大手の不動産会社2社。物件検索、CTA、実績訴求、SEOコンテンツで差別化したい。
決裁者は代表取締役、窓口は営業企画部。初回提案では概算費用とスケジュールも知りたい。`;

type Rank = "A" | "B" | "C" | "D";
type InputMode = "easy" | "detail";
type SampleKind = "renewal" | "recruit" | "lp" | "seo";
type ChatRole = "assistant" | "user";
type ChatAnswerKey = "project" | "company" | "trouble" | "budget" | "deadline" | "competitor";

type EasyInput = {
  projectType: string;
  trouble: string;
  budget: string;
  deadline: string;
  competitorSiteUrl: string;
  currentSiteUrl: string;
  cms: string;
  decisionMakers: string;
  purposes: string[];
};

type MinimalInput = {
  companyName: string;
  goal: string;
  trouble: string;
};

type ChatMessage = {
  id: string;
  role: ChatRole;
  text: string;
};

type ChatQuestion = {
  key: ChatAnswerKey;
  label: string;
  question: string;
  placeholder: string;
};

type ChatAnswers = Partial<Record<ChatAnswerKey, string>>;
type SourceTemplateKind = "readyCrew" | "hearing" | "slack";

type ExtractedInfo = {
  companyName: string;
  contactPerson: string;
  projectContent: string;
  purposes: string[];
  trouble: string;
  budget: string;
  deadline: string;
  competitor: string;
  currentSiteUrl: string;
  cms: string;
  target: string;
  seoIssue: string;
  inquiryDetails: string;
};

type UrlInsight = {
  url: string;
  companyOverview: string;
  business: string;
  strengths: string;
  weaknesses: string;
  competitors: string;
  services: string;
  recruitment: string;
  seoStatus: string;
  improvementPoints: string[];
};

type SalesOpportunityScore = {
  score: number;
  stars: string;
  label: string;
  reasons: string[];
};

type StrategyCard = {
  title: string;
  reason: string;
};

type PreviewSlide = {
  title: string;
  body: string;
};

type QualityScore = {
  total: number;
  proposal: number;
  persuasion: number;
  roi: number;
  differentiation: number;
  readability: number;
  improvements: string[];
};

type DraftEmail = {
  subject: string;
  body: string;
  signature: string;
};

type AiMinutes = {
  minutes: string[];
  todos: string[];
  nextActions: string[];
};

type CoachQuestion = {
  priority: number;
  question: string;
  reason: string;
};

type MeetingEvaluation = {
  total: number;
  hearing: number;
  proposal: number;
  closing: number;
  questions: number;
  information: number;
  comment: string;
  goodPoints: string[];
  improvements: string[];
  nextFocus: string[];
};

type NextMeetingPrep = {
  confirmations: string[];
  homework: string[];
  deliverables: string[];
};

type DailyReport = {
  activities: string[];
  meeting: string[];
  results: string[];
  issues: string[];
  tomorrow: string[];
};

type KnowledgeGroups = {
  similar: HistoryEntry[];
  success: HistoryEntry[];
  lost: HistoryEntry[];
};

type RoleplayScenario = "renewal" | "recruit" | "lp" | "branding";
type RoleplayMessage = {
  role: "customer" | "sales";
  text: string;
};

type WorkMode = "sales" | "coach" | "minutes" | "mail" | "tasks" | "faq" | "summary" | "reports";
type AiEmployeeRole = "secretary" | "sales" | "director" | "writer" | "designer" | "pm";
type AgentStepStatus = "waiting" | "running" | "done";

type GeneratedCounts = Record<WorkMode, number>;

type CompanyResearch = {
  overview: string;
  competitors: string[];
  recruitment: string;
  news: string[];
  services: string[];
  sns: string[];
};

type DigitalAgentStep = {
  label: string;
  detail: string;
  status: AgentStepStatus;
};

type AutomationSettings = {
  morning: boolean;
  weekly: boolean;
  deadline: boolean;
};

type MinutesAiResult = {
  minutes: string[];
  decisions: string[];
  unresolved: string[];
  todos: Array<{ task: string; owner: string; deadline: string }>;
  nextConfirmations: string[];
};

type MailAiResult = {
  subject: string;
  body: string;
  reply: string;
  polite: string;
  short: string;
};

type TaskAiResult = {
  tasks: Array<{ task: string; priority: string; owner: string; deadline: string; risk: string }>;
  nextAction: string;
};

type FaqAiResult = {
  answer: string;
  department: string;
  references: string[];
  notes: string[];
};

type SummaryAiResult = {
  threeLines: string[];
  points: string[];
  actions: string[];
  risks: string[];
  bossSummary: string;
};

type ReportAiResult = {
  daily: string[];
  weekly: string[];
  results: string[];
  issues: string[];
  tomorrow: string[];
  bossMessage: string;
};

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: (() => void) | null;
  start: () => void;
};

const MAX_ASSISTANT_QUESTIONS = 3;

const workModeTabs: Array<{ key: WorkMode; label: string; note: string }> = [
  { key: "sales", label: "営業提案AI", note: "提案書・見積・資料出力" },
  { key: "coach", label: "商談コーチAI", note: "商談前後の支援" },
  { key: "minutes", label: "議事録AI", note: "決定事項とToDo整理" },
  { key: "mail", label: "メール作成AI", note: "件名・本文・返信案" },
  { key: "tasks", label: "タスク整理AI", note: "優先度と期限整理" },
  { key: "faq", label: "社内FAQ AI", note: "回答案と確認先" },
  { key: "summary", label: "資料要約AI", note: "要点とリスク抽出" },
  { key: "reports", label: "日報/週報AI", note: "報告文を作成" }
];

const aiEmployeeRoles: Array<{ key: AiEmployeeRole; label: string; mission: string }> = [
  { key: "secretary", label: "AI秘書", mission: "予定、確認事項、送付メールを整える" },
  { key: "sales", label: "AI営業", mission: "受注確率と提案ストーリーを強化する" },
  { key: "director", label: "AIディレクター", mission: "要件、体制、進行リスクを整理する" },
  { key: "writer", label: "AIライター", mission: "訴求、原稿、メール文を磨く" },
  { key: "designer", label: "AIデザイナー", mission: "見せ方、導線、資料品質を改善する" },
  { key: "pm", label: "AI PM", mission: "見積、スケジュール、タスクを管理する" }
];

const mcpConnectorCards = [
  "Google Drive",
  "GitHub",
  "Notion",
  "Slack",
  "Teams",
  "Google Calendar",
  "Gmail",
  "Outlook",
  "OneDrive",
  "Salesforce",
  "HubSpot",
  "kintone"
];

const initialAgentSteps: DigitalAgentStep[] = [
  { label: "会社調査", detail: "会社URLと案件情報から概要・採用・ニュース・SNS確認観点を整理", status: "waiting" },
  { label: "競合調査", detail: "競合、導線、SEO、CTA、コンテンツ量を比較する観点を作成", status: "waiting" },
  { label: "提案書作成", detail: "提案コンセプト、構成、初稿生成に進む準備", status: "waiting" },
  { label: "見積", detail: "ページ数、CMS、特殊機能、予算感から概算レンジを確認", status: "waiting" },
  { label: "メール", detail: "提案書送付や次回確認依頼のメール文を準備", status: "waiting" }
];

const initialModeCounts: GeneratedCounts = {
  sales: 0,
  coach: 0,
  minutes: 0,
  mail: 0,
  tasks: 0,
  faq: 0,
  summary: 0,
  reports: 0
};

const initialEasyInput: EasyInput = {
  projectType: "",
  trouble: "",
  budget: "未定",
  deadline: "未定",
  competitorSiteUrl: "",
  currentSiteUrl: "",
  cms: "未定",
  decisionMakers: "",
  purposes: []
};

const initialMinimalInput: MinimalInput = {
  companyName: "",
  goal: "",
  trouble: ""
};

const purposeOptions = [
  "問い合わせを増やしたい",
  "採用を強化したい",
  "会社の信頼感を上げたい",
  "更新しやすくしたい",
  "SEOを強化したい"
];

const budgetOptions = ["未定", "100万円未満", "100〜300万円", "300〜500万円", "500万円以上"];
const deadlineOptions = ["未定", "1か月以内", "2〜3か月", "3か月以上"];
const cmsOptions = ["未定", "WordPress", "Movable Type", "独自CMS", "不要"];

const easySamples: Record<SampleKind, EasyInput> = {
  renewal: {
    projectType: "コーポレートサイトのリニューアル",
    trouble: "現行サイトの情報が古く、スマホで物件情報を探しにくい。問い合わせ導線も弱く、地域名検索からの流入を増やしたい。",
    budget: "300〜500万円",
    deadline: "2〜3か月",
    competitorSiteUrl: "https://area-rival-realty.example.jp",
    currentSiteUrl: "https://sample-realty.example.jp",
    cms: "WordPress",
    decisionMakers: "代表取締役、営業企画部",
    purposes: ["問い合わせを増やしたい", "会社の信頼感を上げたい", "更新しやすくしたい", "SEOを強化したい"]
  },
  recruit: {
    projectType: "採用サイト制作",
    trouble: "求人媒体に依存しており、自社の雰囲気や働く魅力が伝わっていない。応募数と応募者の質を改善したい。",
    budget: "100〜300万円",
    deadline: "3か月以上",
    competitorSiteUrl: "https://recruit-rival.example.jp",
    currentSiteUrl: "https://sample-company.example.jp",
    cms: "WordPress",
    decisionMakers: "人事責任者、代表取締役",
    purposes: ["採用を強化したい", "会社の信頼感を上げたい", "更新しやすくしたい"]
  },
  lp: {
    projectType: "新サービスのLP制作",
    trouble: "新サービスの特徴がまだ整理されておらず、広告流入後の問い合わせ率を高めるLPが必要。",
    budget: "100〜300万円",
    deadline: "1か月以内",
    competitorSiteUrl: "https://lp-rival.example.jp",
    currentSiteUrl: "https://sample-service.example.jp",
    cms: "不要",
    decisionMakers: "マーケティング責任者、事業責任者",
    purposes: ["問い合わせを増やしたい", "会社の信頼感を上げたい"]
  },
  seo: {
    projectType: "SEO改善・コンテンツ改善",
    trouble: "自然検索からの流入が伸びておらず、問い合わせにつながる検索キーワードやコンテンツ設計を見直したい。",
    budget: "100〜300万円",
    deadline: "2〜3か月",
    competitorSiteUrl: "https://seo-rival.example.jp",
    currentSiteUrl: "https://sample-seo.example.jp",
    cms: "WordPress",
    decisionMakers: "マーケティング責任者、営業責任者",
    purposes: ["SEOを強化したい", "問い合わせを増やしたい", "更新しやすくしたい"]
  }
};

const chatQuestionFlow: ChatQuestion[] = [
  {
    key: "project",
    label: "案件内容",
    question: "どんな案件ですか？例：コーポレートサイトのリニューアル、採用サイト制作、LP制作など",
    placeholder: "例：不動産会社のWebサイトリニューアルです"
  },
  {
    key: "company",
    label: "お客様",
    question: "お客様はどんな会社ですか？会社名、業種、事業内容が分かる範囲で大丈夫です。",
    placeholder: "例：株式会社サンプル不動産。賃貸・売買仲介を行う会社です"
  },
  {
    key: "trouble",
    label: "困りごと",
    question: "お客様は何に困っていますか？問い合わせ、採用、SEO、更新性など、営業で聞いた内容をそのまま書いてください。",
    placeholder: "例：サイトが古く、問い合わせにつながっていません"
  },
  {
    key: "budget",
    label: "予算",
    question: "予算感は分かりますか？未定でも大丈夫です。",
    placeholder: "例：300万〜500万円、または未定"
  },
  {
    key: "deadline",
    label: "納期",
    question: "公開希望時期や納期はありますか？",
    placeholder: "例：10月末公開希望、または未定"
  },
  {
    key: "competitor",
    label: "競合",
    question: "競合サイトや比較されそうな会社はありますか？URLがあれば貼ってください。",
    placeholder: "例：https://example.co.jp、または競合未確認"
  }
];

const initialChatMessages: ChatMessage[] = [
  {
    id: "assistant-initial",
    role: "assistant",
    text: "こんにちは。AI営業アシスタントです。会話だけで提案書の材料を整理します。まず、どんな案件ですか？"
  }
];

const sourceTemplates: Record<SourceTemplateKind, string> = {
  readyCrew: `Ready Crew案件メールを貼る例：
株式会社サンプル不動産様よりWebサイトリニューアルの相談。
現行サイトが古く、スマホで物件情報を探しにくい。問い合わせ件数を増やしたい。
予算感は300万〜500万円。公開希望は10月末。
CMSはWordPress希望。お知らせ、実績、FAQを更新したい。
競合サイト：https://area-rival-realty.example.jp
既存サイト：https://sample-realty.example.jp
決裁者は代表取締役、窓口は営業企画部。初回提案では概算費用とスケジュールを知りたい。`,
  hearing: `ヒアリングメモを貼る例：
商談メモ
お客様：株式会社サンプル製作所、人事責任者様
相談内容：採用サイトを新しく作りたい。
課題：求人媒体に依存しており、自社の雰囲気や働く魅力が伝わっていない。応募数と応募者の質を改善したい。
目的：採用強化、会社の信頼感向上、更新しやすい採用情報の発信。
予算：100万〜300万円
納期：3か月以上で検討
CMS：WordPress希望
競合：採用競合企業のサイトを参考にしたい。`,
  slack: `Slack相談文を貼る例：
営業相談です。新サービスLP制作の引き合いがありました。
広告流入後の問い合わせ率を上げたいそうです。予算はまだざっくり100〜300万円くらい。
公開はできれば1か月以内。CMSは不要で、問い合わせフォームとCTAを重視。
競合LP：https://lp-rival.example.jp
  原稿作成も相談したいとのこと。`
};

const roleplayScenarios: Record<RoleplayScenario, { label: string; customer: string; firstMessage: string }> = {
  renewal: {
    label: "Webリニューアル案件",
    customer: "不動産会社の営業企画部長",
    firstMessage: "現行サイトが古いのは分かっていますが、どこから直すべきか判断できていません。費用対効果も気になります。"
  },
  recruit: {
    label: "採用サイト案件",
    customer: "採用責任者",
    firstMessage: "応募数も応募者の質も課題です。ただ、採用サイトにどこまで投資すべきか社内で迷っています。"
  },
  lp: {
    label: "LP制作案件",
    customer: "マーケティング責任者",
    firstMessage: "広告流入はありますが、問い合わせにつながりません。短期間で改善したいです。"
  },
  branding: {
    label: "ブランディング案件",
    customer: "代表取締役",
    firstMessage: "会社の強みが伝わっていない気がします。競合と比べて選ばれる理由を明確にしたいです。"
  }
};

type SalesIndicator = {
  title: string;
  rank: Rank;
  label: string;
};

type InfoCheck = {
  key: string;
  label: string;
  found: boolean;
  targetField: string;
  nextQuestion: string;
};

type HearingSheetCategory = {
  key: string;
  category: string;
  found: boolean;
  summary: string;
  questions: string[];
};

type HearingResultSummary = {
  hasInput: boolean;
  minutes: string[];
  decisions: string[];
  unresolved: string[];
  nextConfirmations: string[];
};

type DealEvaluation = {
  rank: Rank;
  probability: number;
  riskScore: number;
  riskLabel: string;
  projectedProbability: number;
  decision: string;
  reason: string;
  positives: string[];
  negatives: string[];
  improvementActions: string[];
};

type CompetitorPoint = {
  label: string;
  point: string;
};

type EstimatePriority = "必須対応" | "推奨対応" | "オプション対応";

type EstimateLine = {
  name: string;
  min: number;
  max: number;
  priority: EstimatePriority;
  enabled: boolean;
};

type EstimateSummary = {
  pageCount: number;
  totalMin: number;
  totalMax: number;
  totalLabel: string;
  budgetAmount: number | null;
  budgetLabel: string;
  budgetFit: "予算内" | "やや調整必要" | "予算超過の可能性あり" | "予算未入力";
  lines: EstimateLine[];
  required: string[];
  recommended: string[];
  optional: string[];
};

type HistoryEntry = {
  id: string;
  createdAt: string;
  title: string;
  clientName: string;
  form: ProposalRequest;
  result: AnalysisResponse;
};

type ProposalPlan = {
  inputInfo: string[];
  outputs: string[];
  aiScope: string[];
  humanScope: string[];
};

type BrowserUsePlan = {
  status: string;
  target: string;
  checks: string[];
  safety: string[];
};

type ConceptBlock = {
  title: string;
  label: string;
  items: string[];
};

type OutputDigestSection = {
  title: string;
  items: string[];
};

type ErrorAdvice = {
  title: string;
  cause: string;
  action: string;
  detail: string;
};

function allInputText(form: ProposalRequest) {
  return [
    form.project_brief,
    form.client_company_info,
    form.competitor_site_url,
    form.competitor_company_name,
    form.estimated_page_count,
    form.cms_required,
    form.contact_form_required,
    form.special_function_required,
    form.seo_required,
    form.content_creation_required,
    form.desired_launch_timing,
    form.budget_range,
    form.hearing_result,
    form.own_service_info,
    form.past_proposal_template,
    form.case_studies
  ].join("\n");
}

function buildEasyMissingItems(easyInput: EasyInput) {
  const missing: string[] = [];
  if (!easyInput.projectType.trim()) {
    missing.push("何を作りたいか");
  }
  if (!easyInput.trouble.trim() && easyInput.purposes.length === 0) {
    missing.push("お客様の困りごと、または目的を1つ以上");
  }
  return missing;
}

function optionalLabel(value: string) {
  return value.trim() || "任意・未入力";
}

function buildProjectBriefFromEasyInput(easyInput: EasyInput) {
  const purposes = easyInput.purposes.length ? easyInput.purposes.join("、") : "未選択";
  return `Ready Crew案件概要：
制作したいものは「${optionalLabel(easyInput.projectType)}」。
目的は、${purposes}。
お客様の困りごとは、${optionalLabel(easyInput.trouble)}。
予算感は「${easyInput.budget}」、納期は「${easyInput.deadline}」。
既存サイトURL：${optionalLabel(easyInput.currentSiteUrl)}
競合サイトURL：${optionalLabel(easyInput.competitorSiteUrl)}
CMS希望：${easyInput.cms}
決裁者・確認者：${optionalLabel(easyInput.decisionMakers)}
初回提案では、課題整理、提案方針、概算見積、スケジュール、PowerPoint提案書の初稿を作成したい。`;
}

function patchFormFromEasyInput(current: ProposalRequest, easyInput: EasyInput): ProposalRequest {
  const nextBrief = buildProjectBriefFromEasyInput(easyInput);
  const currentSiteLine = easyInput.currentSiteUrl.trim() ? `既存サイトURL：${easyInput.currentSiteUrl.trim()}` : "";
  const decisionLine = easyInput.decisionMakers.trim() ? `決裁者・確認者：${easyInput.decisionMakers.trim()}` : "";
  const existingClientInfo = current.client_company_info
    .split("\n")
    .filter((line) => !line.startsWith("既存サイトURL：") && !line.startsWith("決裁者・確認者："))
    .join("\n")
    .trim();
  const clientInfo = [existingClientInfo, currentSiteLine, decisionLine]
    .filter(Boolean)
    .join("\n")
    .trim();

  return {
    ...current,
    project_brief: nextBrief,
    client_company_info: clientInfo,
    competitor_site_url: easyInput.competitorSiteUrl.trim(),
    budget_range: easyInput.budget === "未定" ? "" : easyInput.budget,
    desired_launch_timing: easyInput.deadline === "未定" ? "" : easyInput.deadline,
    cms_required: easyInput.cms,
    seo_required: easyInput.purposes.includes("SEOを強化したい") ? "あり" : current.seo_required,
    contact_form_required: easyInput.purposes.includes("問い合わせを増やしたい") ? "あり" : current.contact_form_required
  };
}

function patchFormFromMinimalInput(current: ProposalRequest, minimalInput: MinimalInput): ProposalRequest {
  const companyName = minimalInput.companyName.trim() || "提案先企業";
  const goal = minimalInput.goal.trim() || "Webサイト制作・改善";
  const trouble = minimalInput.trouble.trim() || "現状課題は要確認";
  return fillMissingProposalForm({
    ...current,
    project_brief: `Ready Crew案件概要：
会社名：${companyName}
やりたいこと：${goal}
困りごと：${trouble}
予算：未定
納期：要確認
CMS：要確認
競合：未確認
決裁者：要確認
ターゲット：要確認
初回提案では、課題整理、提案方針、概算見積、スケジュール、提案書初稿を作成したい。`,
    client_company_info: `${companyName}
担当者・決裁者：要確認
ターゲット：要確認`,
    budget_range: "未定",
    desired_launch_timing: "要確認",
    cms_required: "要確認",
    competitor_company_name: "競合未確認",
    hearing_result: `やりたいこと：${goal}
困りごと：${trouble}
次回確認事項：予算、納期、CMS、競合、決裁者、ターゲット`
  });
}

function extractFirstUrl(value: string | undefined) {
  if (!value) return "";
  return value.match(/https?:\/\/[^\s、。)）]+/)?.[0] ?? "";
}

function extractUrls(value: string | undefined) {
  if (!value) return [];
  return Array.from(new Set(value.match(/https?:\/\/[^\s、。)）]+/g) ?? []));
}

function withoutUrl(value: string | undefined) {
  if (!value) return "";
  return value.replace(/https?:\/\/[^\s、。)）]+/g, "").replace(/[、。,\s]+$/g, "").trim();
}

function isUnknownAnswer(value: string | undefined) {
  return !value?.trim() || /未定|不明|未確認|なし|まだ/.test(value);
}

function buildProjectBriefFromChatAnswers(answers: ChatAnswers) {
  const project = answers.project?.trim() || "未確認";
  const company = answers.company?.trim() || "未確認";
  const trouble = answers.trouble?.trim() || "未確認";
  const budget = answers.budget?.trim() || "未確認";
  const deadline = answers.deadline?.trim() || "未確認";
  const competitor = answers.competitor?.trim() || "未確認";

  return `AI営業アシスタント整理内容：
案件内容：${project}
お客様情報：${company}
お客様の困りごと：${trouble}
予算感：${budget}
公開希望時期・納期：${deadline}
競合情報：${competitor}
提案書では、現状理解、課題整理、Web戦略、競合比較、概算見積、スケジュール、体制、今後の進め方を整理する。`;
}

function compactText(value: string) {
  return value.replace(/\r/g, "").replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
}

function findLabeledValue(text: string, labels: string[]) {
  const lines = compactText(text).split("\n").map((line) => line.trim()).filter(Boolean);
  for (const label of labels) {
    const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const direct = lines.find((line) => new RegExp(`^${escaped}\\s*[:：]\\s*`, "i").test(line));
    if (direct) {
      return direct.replace(new RegExp(`^${escaped}\\s*[:：]\\s*`, "i"), "").trim();
    }
    const included = lines.find((line) => line.includes(label) && /[:：]/.test(line));
    if (included) {
      return included.split(/[:：]/).slice(1).join("：").trim();
    }
  }
  return "";
}

function findSentence(text: string, patterns: (RegExp | string)[]) {
  const sentences = compactText(text)
    .split(/[\n。！？!?]/)
    .map((line) => line.trim())
    .filter(Boolean);
  return sentences.find((sentence) => hasAny(sentence, patterns)) ?? "";
}

function extractCompanyName(text: string, fallbackUrl = "") {
  const labeled = findLabeledValue(text, ["会社名", "企業名", "顧客名", "社名", "提案先", "お客様"]);
  if (labeled) return labeled;
  const match = text.match(/(?:株式会社|有限会社|合同会社|医療法人|学校法人|社会福祉法人)[^\s　、。:：\n]{1,30}/);
  if (match) return match[0];
  if (fallbackUrl) {
    try {
      return new URL(fallbackUrl).hostname.replace(/^www\./, "");
    } catch {
      return "";
    }
  }
  return "";
}

function extractPurposeList(text: string) {
  const candidates = [
    { keyword: /問い合わせ|問合せ|資料請求|来店予約|CV|コンバージョン/i, label: "問い合わせを増やしたい" },
    { keyword: /採用|応募|求人|人材/i, label: "採用を強化したい" },
    { keyword: /信頼|ブランド|ブランディング|認知|実績/i, label: "会社の信頼感を上げたい" },
    { keyword: /更新|CMS|お知らせ|ブログ|運用/i, label: "更新しやすくしたい" },
    { keyword: /SEO|検索|自然流入|流入|順位/i, label: "SEOを強化したい" }
  ];
  return candidates.filter((item) => item.keyword.test(text)).map((item) => item.label);
}

function extractProposalInfo(rawText: string, homepageUrl: string): ExtractedInfo {
  const text = compactText(rawText);
  const urls = extractUrls(`${text}\n${homepageUrl}`);
  const competitorLine = findSentence(text, ["競合", "比較", "他社"]);
  const currentSiteLine = findSentence(text, ["既存サイト", "現行サイト", "会社HP", "ホームページURL", "URL"]);
  const budget =
    findLabeledValue(text, ["予算", "予算感", "費用", "金額"]) ||
    text.match(/\d{2,4}\s*万\s*(?:円)?\s*[〜~～-]\s*\d{2,4}\s*万\s*円?/)?.[0] ||
    text.match(/\d{2,4}\s*万円(?:以内|程度|前後)?/)?.[0] ||
    "";
  const deadline =
    findLabeledValue(text, ["納期", "公開希望", "公開時期", "希望時期", "リリース"]) ||
    text.match(/\d{4}年\d{1,2}月(?:末|中|上旬|下旬)?/)?.[0] ||
    text.match(/\d{1,2}月(?:末|中|上旬|下旬)?/)?.[0] ||
    "";
  const projectContent =
    findLabeledValue(text, ["案件内容", "依頼内容", "相談内容", "制作内容", "概要"]) ||
    findSentence(text, ["リニューアル", "制作", "LP", "採用サイト", "Webサイト", "ホームページ", "コーポレートサイト"]);
  const trouble =
    findLabeledValue(text, ["課題", "困りごと", "悩み", "現状", "背景"]) ||
    findSentence(text, [/困|課題|古い|弱い|不足|できていない|伸びない|少ない|改善/]);
  const cms =
    findLabeledValue(text, ["CMS", "CMS希望", "更新"]) ||
    text.match(/WordPress|Movable Type|独自CMS|CMS不要|CMSあり/i)?.[0] ||
    "";
  const target =
    findLabeledValue(text, ["ターゲット", "対象", "ユーザー", "顧客", "求職者"]) ||
    findSentence(text, ["ターゲット", "ユーザー", "顧客", "求職者", "学生", "法人", "個人"]);
  const seoIssue =
    findLabeledValue(text, ["SEO課題", "SEO", "検索課題"]) ||
    findSentence(text, ["SEO", "検索", "自然流入", "順位", "流入"]);
  const inquiryDetails =
    findLabeledValue(text, ["問い合わせ内容", "相談内容", "要望", "希望"]) ||
    findSentence(text, ["知りたい", "相談", "依頼", "提案", "見積", "スケジュール"]);
  const competitorUrl = extractFirstUrl(competitorLine);
  const currentSiteUrl = homepageUrl.trim() || extractFirstUrl(currentSiteLine) || urls.find((url) => url !== competitorUrl) || "";

  return {
    companyName: extractCompanyName(text, currentSiteUrl),
    contactPerson: findLabeledValue(text, ["担当者", "窓口", "ご担当", "決裁者", "確認者"]),
    projectContent,
    purposes: extractPurposeList(text),
    trouble,
    budget,
    deadline,
    competitor: competitorLine || competitorUrl || findLabeledValue(text, ["競合", "競合サイト", "競合企業"]),
    currentSiteUrl,
    cms,
    target,
    seoIssue,
    inquiryDetails
  };
}

function buildUrlInsight(url: string, rawText: string, extracted: ExtractedInfo): UrlInsight | null {
  const targetUrl = url.trim() || extracted.currentSiteUrl.trim();
  if (!targetUrl) return null;
  let hostname = targetUrl;
  try {
    hostname = new URL(targetUrl).hostname.replace(/^www\./, "");
  } catch {
    hostname = targetUrl.replace(/^https?:\/\//, "").split("/")[0];
  }
  const text = `${rawText}\n${extracted.projectContent}\n${extracted.trouble}`;
  const isRecruit = /採用|求人|応募|人材/.test(text);
  const isRealEstate = /不動産|物件|賃貸|売買|住宅/.test(text);
  const isLp = /LP|ランディング|広告|CPA|資料請求/.test(text);

  return {
    url: targetUrl,
    companyOverview: `${extracted.companyName || hostname}の公開サイトとして、事業理解・信頼形成・問い合わせ導線の確認対象にします。`,
    business: isRealEstate
      ? "不動産・住宅領域のサービス訴求、物件情報、来店・問い合わせ獲得が中心と想定します。"
      : isRecruit
        ? "採用広報、職種理解、応募導線、社員紹介を中心に整理します。"
        : "サービス紹介、実績訴求、問い合わせ獲得を中心に整理します。",
    strengths: "既存の事業実績、専門性、地域性、顧客対応力を強みとして提案に転換します。",
    weaknesses: "サイト上で強み・実績・問い合わせ導線が分散している前提で、訴求整理と導線短縮を改善ポイントにします。",
    competitors: extracted.competitor || "競合未確認。次回ヒアリングで比較対象サイトを確認します。",
    services: isLp ? "新サービスの価値訴求、CTA、フォーム導線を重点確認します。" : "主要サービス、料金・事例・FAQ・問い合わせ導線を確認対象にします。",
    recruitment: isRecruit ? "採用情報、社員インタビュー、働く環境、応募導線を重点的に改善します。" : "採用情報がある場合は、信頼感と企業理解を補強する要素として扱います。",
    seoStatus: /SEO|検索|自然流入|流入/.test(text)
      ? "検索流入強化が論点に含まれるため、カテゴリ設計・見出し・FAQ・事例コンテンツを強化します。"
      : "現時点ではSEO要件が未確定のため、基本的なサイト構造・タイトル・導線改善を初期提案に含めます。",
    improvementPoints: [
      "ファーストビューで提供価値とCTAを明確化",
      "サービス・実績・FAQから問い合わせまでの導線を短縮",
      "CMS更新しやすい情報設計とSEOに強いコンテンツ構造を提案"
    ]
  };
}

function hostnameFromUrl(value: string) {
  if (!value.trim()) return "";
  try {
    return new URL(value.trim()).hostname.replace(/^www\./, "");
  } catch {
    return value.replace(/^https?:\/\//, "").split("/")[0];
  }
}

function fillMissingExtractedInfo(info: ExtractedInfo, homepageUrl: string): ExtractedInfo {
  const fallbackHost = hostnameFromUrl(homepageUrl || info.currentSiteUrl);
  return {
    ...info,
    companyName: info.companyName || fallbackHost || "提案先企業",
    contactPerson: info.contactPerson || "要確認",
    projectContent: info.projectContent || "Webサイト制作・改善提案",
    purposes: info.purposes.length ? info.purposes : ["問い合わせを増やしたい"],
    trouble: info.trouble || "現状課題は要確認。初回提案ではWebサイトの改善余地を整理します。",
    budget: info.budget || "未定",
    deadline: info.deadline || "要確認",
    competitor: info.competitor || "競合未確認",
    currentSiteUrl: info.currentSiteUrl || homepageUrl.trim(),
    cms: info.cms || "要確認",
    target: info.target || "要確認",
    seoIssue: info.seoIssue || "要確認",
    inquiryDetails: info.inquiryDetails || "提案内容、概算費用、スケジュールを確認したい"
  };
}

function fillMissingProposalForm(form: ProposalRequest): ProposalRequest {
  const hasCompetitor = Boolean(form.competitor_site_url.trim() || form.competitor_company_name.trim());
  const hasDecisionMaker = /決裁者|確認者|担当者/.test(form.client_company_info) || /決裁者|確認者|担当者/.test(form.project_brief);
  const hasTarget = /ターゲット|対象|顧客|求職者|ユーザー/.test(allInputText(form));
  const clientCompanyInfo = form.client_company_info.trim() || "提案先企業";
  return {
    ...form,
    project_brief:
      form.project_brief.trim() ||
      "Webサイト制作・改善提案。詳細条件は要確認として、提案書初稿を作成します。",
    client_company_info: [
      clientCompanyInfo,
      hasDecisionMaker ? "" : "担当者・決裁者：要確認",
      hasTarget ? "" : "ターゲット：要確認"
    ]
      .filter(Boolean)
      .join("\n"),
    budget_range: form.budget_range.trim() || "未定",
    desired_launch_timing: form.desired_launch_timing.trim() || "要確認",
    cms_required: form.cms_required.trim() || "要確認",
    competitor_company_name: hasCompetitor ? form.competitor_company_name : "競合未確認",
    hearing_result:
      form.hearing_result.trim() ||
      "未入力項目は次回確認事項として扱い、初回提案では仮説ベースで整理します。"
  };
}

function buildChatAnswersFromExtracted(info: ExtractedInfo): ChatAnswers {
  return {
    ...(info.projectContent ? { project: info.projectContent } : {}),
    ...(info.companyName || info.contactPerson || info.currentSiteUrl
      ? { company: [info.companyName, info.contactPerson ? `担当者：${info.contactPerson}` : "", info.currentSiteUrl ? `URL：${info.currentSiteUrl}` : ""].filter(Boolean).join("。") }
      : {}),
    ...(info.trouble || info.purposes.length ? { trouble: [info.trouble, info.purposes.length ? `目的：${info.purposes.join("、")}` : ""].filter(Boolean).join("。") } : {}),
    ...(info.budget ? { budget: info.budget } : {}),
    ...(info.deadline ? { deadline: info.deadline } : {}),
    ...(info.competitor ? { competitor: info.competitor } : {})
  };
}

function buildFormFromExtracted(current: ProposalRequest, info: ExtractedInfo, insight: UrlInsight | null): ProposalRequest {
  const answers = buildChatAnswersFromExtracted(info);
  const next = applyChatAnswersToForm(current, answers);
  const urlInsightText = insight
    ? `URL解析メモ：
会社概要：${insight.companyOverview}
事業内容：${insight.business}
強み：${insight.strengths}
サービス：${insight.services}
採用情報：${insight.recruitment}
SEO状況：${insight.seoStatus}
弱み：${insight.weaknesses}
競合：${insight.competitors}
改善ポイント：${insight.improvementPoints.join("、")}`
    : "";

  return {
    ...next,
    project_brief: `${next.project_brief}
抽出元情報：
目的：${info.purposes.join("、") || "未抽出"}
ターゲット：${info.target || "未抽出"}
SEO課題：${info.seoIssue || "未抽出"}
問い合わせ内容：${info.inquiryDetails || "未抽出"}
CMS：${info.cms || "未抽出"}
${urlInsightText}`.trim(),
    client_company_info: [
      info.companyName,
      info.contactPerson ? `担当者・確認者：${info.contactPerson}` : "",
      info.currentSiteUrl ? `会社ホームページURL：${info.currentSiteUrl}` : "",
      insight?.companyOverview,
      insight?.business,
      insight?.strengths
    ].filter(Boolean).join("\n"),
    cms_required: info.cms || next.cms_required,
    competitor_site_url: extractFirstUrl(info.competitor) || next.competitor_site_url,
    budget_range: info.budget || next.budget_range,
    desired_launch_timing: info.deadline || next.desired_launch_timing,
    hearing_result: [current.hearing_result, info.inquiryDetails, urlInsightText].filter(Boolean).join("\n\n")
  };
}

function findNextMissingQuestionIndex(answers: ChatAnswers) {
  return chatQuestionFlow.findIndex((question) => !answers[question.key]?.trim());
}

function applyChatAnswersToForm(current: ProposalRequest, answers: ChatAnswers): ProposalRequest {
  const allText = Object.values(answers).filter(Boolean).join("\n");
  const competitorUrl = extractFirstUrl(answers.competitor);
  const competitorName = withoutUrl(answers.competitor);

  return {
    ...current,
    project_brief: buildProjectBriefFromChatAnswers(answers),
    client_company_info: answers.company?.trim() || current.client_company_info,
    competitor_site_url: competitorUrl || current.competitor_site_url,
    competitor_company_name: competitorName || current.competitor_company_name,
    budget_range: isUnknownAnswer(answers.budget) ? current.budget_range : answers.budget?.trim() || current.budget_range,
    desired_launch_timing: isUnknownAnswer(answers.deadline) ? current.desired_launch_timing : answers.deadline?.trim() || current.desired_launch_timing,
    cms_required: /cms|wordpress|movable type|更新|お知らせ|ブログ/i.test(allText) ? "あり" : current.cms_required,
    contact_form_required: /問い合わせ|問合せ|フォーム|cta|資料請求|来店予約/i.test(allText) ? "あり" : current.contact_form_required,
    seo_required: /seo|検索|自然流入|流入|順位/i.test(allText) ? "あり" : current.seo_required,
    special_function_required: /物件検索|予約|会員|検索機能|絞り込み|シミュレーション/i.test(allText)
      ? "特殊機能あり"
      : current.special_function_required
  };
}

function buildChatReadiness(answers: ChatAnswers) {
  const required: Array<{ key: ChatAnswerKey; label: string }> = [
    { key: "project", label: "案件内容" },
    { key: "company", label: "お客様情報" },
    { key: "trouble", label: "困りごと" }
  ];
  const missing = required.filter((item) => !answers[item.key]?.trim()).map((item) => item.label);
  const answeredCount = chatQuestionFlow.filter((item) => answers[item.key]?.trim()).length;

  return {
    ready: missing.length === 0,
    missing,
    answeredCount,
    totalCount: chatQuestionFlow.length
  };
}

function buildLiveProjectSummary(form: ProposalRequest, missingItems: InfoCheck[]): OutputDigestSection[] {
  const brief = form.project_brief.trim().replace(/\s+/g, " ");
  return [
    {
      title: "現在の案件概要",
      items: [
        brief ? `${brief.slice(0, 150)}${brief.length > 150 ? "..." : ""}` : "チャットで回答すると、ここに案件概要が自動整理されます。"
      ]
    },
    {
      title: "整理済み情報",
      items: [
        `提案先: ${extractClientName(form)}`,
        `予算: ${form.budget_range.trim() || "未確認"}`,
        `納期: ${form.desired_launch_timing.trim() || "未確認"}`,
        `競合: ${form.competitor_site_url.trim() || form.competitor_company_name.trim() || "未確認"}`
      ]
    },
    {
      title: "次回確認事項",
      items: missingItems.length
        ? missingItems.slice(0, 4).map((item) => `${item.label}: ${item.nextQuestion}`)
        : ["提案書を生成できます。内容確認後、PPTX・PDF出力へ進めます。"]
    }
  ];
}

function buildSalesOpportunityScore(form: ProposalRequest, checks: InfoCheck[]): SalesOpportunityScore {
  const text = allInputText(form);
  let score = 2;
  const reasons: string[] = [];

  if (form.project_brief.trim().length >= 40) {
    score += 1;
    reasons.push("案件内容が整理されています");
  }
  if (checks.find((item) => item.key === "budget")?.found) {
    score += 1;
    reasons.push("予算感が確認できています");
  }
  if (checks.find((item) => item.key === "deadline")?.found) {
    score += 1;
    reasons.push("納期・公開希望が確認できています");
  }
  if (checks.find((item) => item.key === "decision-maker")?.found) {
    score += 1;
    reasons.push("決裁者・確認者の情報があります");
  }
  if (/問い合わせ|採用|SEO|リニューアル|CMS|資料請求|CV/.test(text)) {
    score += 1;
    reasons.push("提案テーマが具体的です");
  }
  if (/未定|未確認|不明/.test(text)) {
    score -= 1;
    reasons.push("未確認情報が残っています");
  }

  const normalizedScore = Math.max(1, Math.min(5, score));
  return {
    score: normalizedScore,
    stars: "★★★★★".slice(0, normalizedScore) + "☆☆☆☆☆".slice(0, 5 - normalizedScore),
    label: normalizedScore >= 4 ? "案件化しやすい" : normalizedScore >= 3 ? "追加確認で案件化しやすい" : "要ヒアリング",
    reasons: reasons.length ? reasons.slice(0, 4) : ["案件内容、予算、納期、決裁者を確認すると判断しやすくなります"]
  };
}

function buildAiRecommendations(form: ProposalRequest, insight: UrlInsight | null) {
  const text = allInputText(form);
  const recommendations: string[] = [];

  if (/問い合わせ|資料請求|CV|コンバージョン|来店予約/.test(text)) {
    recommendations.push("問い合わせ最大化提案：ファーストビュー、CTA、フォーム導線、FAQを改善してCVまでの迷いを減らします。");
  }
  if (/採用|求人|応募|人材/.test(text)) {
    recommendations.push("採用強化提案：職種理解、社員紹介、働く環境、応募導線を整えて応募前の不安を減らします。");
  }
  if (/SEO|検索|自然流入|流入|地域名/.test(text)) {
    recommendations.push("SEO強化提案：サービス別・課題別・FAQ・実績コンテンツを増やし、検索流入から問い合わせへつなげます。");
  }
  if (/CMS|更新|お知らせ|ブログ|運用/.test(text)) {
    recommendations.push("CMS運用提案：更新しやすい管理画面と投稿ルールを設計し、公開後の改善運用を回せる状態にします。");
  }
  if (/競合|比較|他社/.test(text) || form.competitor_site_url.trim()) {
    recommendations.push("競合差別化提案：競合より分かりやすい導線、実績訴求、CTA配置で選ばれる理由を明確にします。");
  }
  if (insight) {
    recommendations.push(`URL改善提案：${insight.improvementPoints[0]}し、既存サイトの強みを提案ストーリーへ反映します。`);
  }

  return uniqueTextItems(recommendations).slice(0, 3).length
    ? uniqueTextItems(recommendations).slice(0, 3)
    : [
        "現状理解提案：事業内容と顧客課題を整理し、提案サマリーで意思決定しやすくします。",
        "導線改善提案：主要CTAと問い合わせフォームまでの流れを短くし、成果につながる構成にします。",
        "運用改善提案：CMSと改善レポートを前提に、公開後も成果を伸ばす提案にします。"
      ];
}

function buildStrategyCards(form: ProposalRequest, recommendations: string[]): StrategyCard[] {
  const text = allInputText(form);
  const cards: StrategyCard[] = [];

  if (/デザイン|古い|信頼|ブランド|ブランディング|見た目/.test(text)) {
    cards.push({ title: "デザイン重視", reason: "信頼感や第一印象の改善が成果に直結するため、ファーストビューと実績訴求を強化します。" });
  }
  if (/SEO|検索|自然流入|流入|地域名/.test(text)) {
    cards.push({ title: "SEO重視", reason: "検索流入が課題に含まれるため、サービス別・FAQ・事例コンテンツで入口を増やします。" });
  }
  if (/採用|求人|応募|人材/.test(text)) {
    cards.push({ title: "採用強化", reason: "応募前の不安を減らすため、社員紹介・職種紹介・働く環境を分かりやすくします。" });
  }
  if (/問い合わせ|資料請求|CV|CTA|来店予約/.test(text)) {
    cards.push({ title: "問い合わせ最大化", reason: "問い合わせ導線が成果に直結するため、CTA配置とフォーム到達までの流れを短縮します。" });
  }
  if (/競合|比較|他社/.test(text)) {
    cards.push({ title: "差別化重視", reason: "競合比較が想定されるため、選ばれる理由と実績訴求を明確にします。" });
  }

  recommendations.forEach((item) => {
    if (cards.length < 3) {
      const [title, reason] = item.split("：");
      cards.push({ title: title || "提案強化", reason: reason || item });
    }
  });

  return cards.slice(0, 3);
}

function buildPreviewSlides(form: ProposalRequest, strategies: StrategyCard[], estimate: EstimateSummary): PreviewSlide[] {
  const client = extractClientName(form);
  return [
    { title: `${client} Webサイト制作ご提案`, body: "現状理解から課題、戦略、制作方針、費用、進め方までを整理します。" },
    { title: "提案サマリー", body: form.project_brief.trim().slice(0, 180) || "案件メールの内容をもとに提案サマリーを整理します。" },
    { title: "現状理解・課題", body: form.hearing_result.trim().slice(0, 180) || "不足情報は次回確認事項として扱い、仮説ベースで課題を整理します。" },
    { title: "AI提案戦略", body: strategies.map((item) => `${item.title}: ${item.reason}`).join("\n") },
    { title: "競合・SEO方針", body: `競合: ${form.competitor_site_url || form.competitor_company_name || "競合未確認"}\nSEO: ${form.seo_required || "要確認"}` },
    { title: "概算見積・スケジュール", body: `概算見積: ${estimate.totalLabel}\n予算適合: ${estimate.budgetFit}\n納期: ${form.desired_launch_timing || "要確認"}` },
    { title: "今後の進め方", body: "不足情報確認、要件定義、構成案作成、デザイン制作、実装、検証、公開の順で進行します。" }
  ];
}

function buildQualityScore(
  result: AnalysisResponse | null,
  form: ProposalRequest,
  deal: DealEvaluation,
  estimate: EstimateSummary,
  strategies: StrategyCard[]
): QualityScore {
  const hasResult = Boolean(result);
  const proposal = Math.min(100, 62 + strategies.length * 8 + (form.project_brief.length > 120 ? 12 : 0));
  const persuasion = Math.min(100, 58 + deal.positives.length * 7 + (form.case_studies.trim() ? 12 : 0));
  const roi = Math.min(100, 55 + (estimate.budgetFit === "予算内" ? 18 : estimate.budgetFit === "やや調整必要" ? 10 : 4));
  const differentiation = Math.min(100, 56 + (form.competitor_site_url || form.competitor_company_name ? 18 : 6) + strategies.length * 4);
  const readability = Math.min(100, hasResult ? 82 : 72);
  const total = Math.round((proposal + persuasion + roi + differentiation + readability) / 5);
  const improvements = [
    form.case_studies.trim() ? "成功事例の成果数値を表紙直後の提案サマリーにも反映します。" : "類似実績を1〜2件追加すると説得力が上がります。",
    form.budget_range.trim() && form.budget_range !== "未定" ? "予算内・オプションの切り分けを明確にします。" : "予算確認後、必須範囲とオプション範囲を再整理します。",
    form.competitor_site_url.trim() ? "競合サイトのCTA・SEO・実績訴求を実画面で確認します。" : "競合サイトURLを確認すると差別化提案が強くなります。"
  ];

  return { total, proposal, persuasion, roi, differentiation, readability, improvements };
}

function buildDraftEmail(form: ProposalRequest): DraftEmail {
  const client = extractClientName(form);
  return {
    subject: `【ご提案資料送付】${client} Webサイト制作のご提案`,
    body: `${client}
ご担当者様

お世話になっております。
Webサイト制作のご相談について、初回提案資料をお送りします。

本資料では、現状理解、想定課題、提案方針、概算費用、スケジュールを整理しております。
未確認事項については、次回のお打ち合わせで確認させてください。

ご確認のほど、よろしくお願いいたします。`,
    signature: "Ready Crew Proposal AI\n営業担当"
  };
}

function buildAiMinutes(form: ProposalRequest, extracted: ExtractedInfo | null): AiMinutes {
  const source = form.hearing_result.trim() || form.project_brief.trim();
  const minutes = [
    `${extractClientName(form)}の相談内容を確認`,
    extracted?.projectContent || "Webサイト制作・改善提案について協議",
    extracted?.trouble || "現状課題と改善方針を整理"
  ];
  const todos = [
    form.budget_range && form.budget_range !== "未定" ? "予算範囲に合わせた提案範囲を調整" : "予算感を確認",
    form.desired_launch_timing && form.desired_launch_timing !== "要確認" ? "公開希望時期から逆算してスケジュール作成" : "公開希望時期を確認",
    form.competitor_site_url || form.competitor_company_name ? "競合比較観点を提案書に反映" : "競合サイトを確認"
  ];
  const nextActions = [
    "提案書初稿を確認",
    "不足情報を次回ヒアリングで確認",
    source ? "提案範囲・費用・スケジュールを合意形成" : "案件メールまたは商談メモを追加"
  ];

  return { minutes, todos, nextActions };
}

function buildWinRateImprovements(deal: DealEvaluation, quality: QualityScore) {
  return [
    `決裁者・予算・納期の確認で受注確率を${deal.probability}%から${deal.projectedProbability}%へ引き上げます。`,
    quality.roi < 75 ? "費用対効果の説明を追加し、必須範囲とオプション範囲を分けます。" : "ROI説明は十分です。成果指標を提案サマリーに強調します。",
    quality.differentiation < 80 ? "競合比較を1枚追加し、勝ち筋を明確にします。" : "競合差別化の軸を維持し、実績訴求を強めます。"
  ];
}

function buildSimilarCases(history: HistoryEntry[], form: ProposalRequest) {
  const text = allInputText(form);
  const keywords = ["不動産", "採用", "LP", "SEO", "CMS", "問い合わせ", "リニューアル", "物件", "資料請求"];
  return history
    .map((entry) => {
      const entryText = allInputText(entry.form);
      const score = keywords.reduce((sum, keyword) => sum + (text.includes(keyword) && entryText.includes(keyword) ? 1 : 0), 0);
      return { entry, score };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);
}

function buildDashboardMetrics(history: HistoryEntry[], result: AnalysisResponse | null) {
  const today = new Date().toDateString();
  const todayCount = history.filter((entry) => new Date(entry.createdAt).toDateString() === today).length + (result ? 1 : 0);
  const proposalCount = history.length + (result ? 1 : 0);
  const savedHours = Math.max(0, Math.round(proposalCount * 2.2 * 10) / 10);

  return [
    { label: "本日の案件数", value: `${todayCount}件`, note: "今日整理した案件" },
    { label: "提案書作成数", value: `${proposalCount}件`, note: "Markdown / PPTX生成" },
    { label: "生成履歴", value: `${history.length}件`, note: "ローカル保存" },
    { label: "平均作成時間", value: "20分", note: "従来2〜3時間から短縮" },
    { label: "AI削減時間", value: `${savedHours}h`, note: "累計目安" }
  ];
}

function buildMonthlyDashboardMetrics(history: HistoryEntry[], result: AnalysisResponse | null, quality: QualityScore, deal: DealEvaluation) {
  const now = new Date();
  const monthEntries = history.filter((entry) => {
    const date = new Date(entry.createdAt);
    return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth();
  });
  const proposalCount = monthEntries.length + (result ? 1 : 0);
  const winCount = monthEntries.filter((entry) => (entry.result.analysis.win_probability.probability ?? 0) >= 70).length + (deal.probability >= 70 ? 1 : 0);
  const avgProbability = proposalCount
    ? Math.round(
        (monthEntries.reduce((sum, entry) => sum + (entry.result.analysis.win_probability.probability ?? 0), 0) + deal.probability) /
          proposalCount
      )
    : deal.probability;
  return [
    { label: "今月提案数", value: `${proposalCount}件`, note: "今月の提案準備" },
    { label: "今月受注数", value: `${winCount}件`, note: "70%以上を受注見込みで計上" },
    { label: "AI削減時間", value: `${Math.round(proposalCount * 2.2 * 10) / 10}h`, note: "今月の削減目安" },
    { label: "平均品質スコア", value: `${quality.total}点`, note: "現在案件を基準表示" },
    { label: "平均受注確率", value: `${avgProbability}%`, note: "履歴と現在案件の平均" }
  ];
}

function buildPreMeetingChecklist(checks: InfoCheck[]) {
  const found = new Map(checks.map((item) => [item.key, item.found]));
  return [
    { label: "この会社の事業内容を理解していますか", done: Boolean(found.get("current-site")) },
    { label: "競合を確認しましたか", done: Boolean(found.get("competitor")) },
    { label: "予算を確認しましたか", done: Boolean(found.get("budget")) },
    { label: "納期を確認しましたか", done: Boolean(found.get("deadline")) },
    { label: "決裁者を確認しましたか", done: Boolean(found.get("decision-maker")) },
    { label: "CMS希望を確認しましたか", done: Boolean(found.get("cms")) }
  ];
}

function buildCoachQuestions(form: ProposalRequest, missingItems: InfoCheck[]): CoachQuestion[] {
  const text = allInputText(form);
  const base: CoachQuestion[] = [
    { priority: 5, question: "最終決裁者はどなたですか？", reason: "提案後の意思決定ルートを確認するため" },
    { priority: 5, question: "今回のWeb制作で最も達成したい成果は何ですか？", reason: "提案軸とKPIを合わせるため" },
    { priority: 4, question: "予算の上限と、段階提案の可否を教えてください。", reason: "必須範囲とオプションを分けるため" },
    { priority: 4, question: "公開希望日は必達ですか、それとも目安ですか？", reason: "スケジュールリスクを判断するため" },
    { priority: 4, question: "公開後の更新担当者はいますか？", reason: "CMSと運用体制を設計するため" },
    { priority: 4, question: "競合サイトで良いと思う点・避けたい点はありますか？", reason: "差別化と好みを把握するため" },
    { priority: 3, question: "現在のサイトで一番困っているページはどこですか？", reason: "改善優先度を決めるため" },
    { priority: 3, question: "問い合わせや応募の現在数と目標数はありますか？", reason: "成果指標とROIを提示するため" },
    { priority: 3, question: "写真撮影・原稿作成は社内対応できますか？", reason: "制作範囲と見積精度を上げるため" },
    { priority: 3, question: "社内確認に必要な人数と確認期間を教えてください。", reason: "手戻りと納期遅延を防ぐため" }
  ];

  const missingBoost = missingItems.map((item) => ({
    priority: 5,
    question: `${item.label}について確認してください。${item.nextQuestion}は分かりますか？`,
    reason: "不足情報を埋めると提案精度が上がるため"
  }));
  const industryQuestion = /採用|求人|応募/.test(text)
    ? [{ priority: 5, question: "採用したい職種と応募者像を教えてください。", reason: "採用サイトの訴求軸を決めるため" }]
    : /不動産|物件/.test(text)
      ? [{ priority: 5, question: "物件情報の登録・検索・更新はどのように運用していますか？", reason: "物件検索やCMS要件を決めるため" }]
      : [];

  return uniqueTextItems([...industryQuestion, ...missingBoost, ...base].map((item) => `${item.priority}|${item.question}|${item.reason}`))
    .map((item) => {
      const [priority, question, reason] = item.split("|");
      return { priority: Number(priority), question, reason };
    })
    .sort((a, b) => b.priority - a.priority)
    .slice(0, 10);
}

function starsFromPriority(priority: number) {
  const normalized = Math.max(1, Math.min(5, priority));
  return `${"★".repeat(normalized)}${"☆".repeat(5 - normalized)}`;
}

function buildRealtimeQuestion(liveMemo: string, questions: CoachQuestion[]) {
  const text = liveMemo || "";
  if (!text.trim()) return questions[0]?.question ?? "まず現状課題を確認しましょう。";
  if (!/予算|費用|金額/.test(text)) return "予算感と上限、段階提案の可否を確認しましょう。";
  if (!/納期|公開|いつ|時期/.test(text)) return "公開希望時期と必達期限を確認しましょう。";
  if (!/決裁|承認|社長|代表|役員/.test(text)) return "決裁者と承認フローを確認しましょう。";
  if (!/競合|比較|他社/.test(text)) return "比較している競合サイトや参考サイトを確認しましょう。";
  if (!/KPI|目標|問い合わせ|応募|CV/.test(text)) return "成果目標やKPIを数字で確認しましょう。";
  return "最後に、次回までの提出物と確認スケジュールを合意しましょう。";
}

function buildMeetingEvaluation(memo: string, form: ProposalRequest): MeetingEvaluation {
  const text = `${memo}\n${allInputText(form)}`;
  const hearing = Math.min(100, 50 + ["予算", "納期", "決裁", "競合", "CMS", "KPI"].filter((word) => text.includes(word)).length * 8);
  const proposal = Math.min(100, 55 + ["提案", "改善", "SEO", "CTA", "CMS", "運用"].filter((word) => text.includes(word)).length * 7);
  const closing = Math.min(100, 48 + ["次回", "提出", "確認", "合意", "スケジュール"].filter((word) => text.includes(word)).length * 9);
  const questions = Math.min(100, 52 + (memo.match(/？|\?/g)?.length ?? 0) * 8 + ["誰", "いつ", "いくら", "どの"].filter((word) => text.includes(word)).length * 6);
  const information = Math.min(100, 50 + ["会社", "担当", "目的", "課題", "予算", "納期", "競合", "運用"].filter((word) => text.includes(word)).length * 6);
  const total = Math.round((hearing + proposal + closing + questions + information) / 5);

  return {
    total,
    hearing,
    proposal,
    closing,
    questions,
    information,
    comment: total >= 80 ? "商談情報が十分に整理されています。提案書の説得力を高められます。" : total >= 65 ? "基本情報は取れています。不足条件を追加確認すると受注確度が上がります。" : "商談情報がまだ薄い状態です。次回は予算・納期・決裁者を優先確認しましょう。",
    goodPoints: [
      text.includes("課題") || text.includes("困") ? "課題を確認できています" : "提案に必要な会話の土台を作れています",
      text.includes("予算") ? "予算に触れられています" : "提案範囲の相談に進めています",
      text.includes("次回") ? "次回アクションを意識できています" : "提案準備へ進める情報があります"
    ],
    improvements: [
      text.includes("決裁") ? "決裁者情報を提案書にも反映しましょう" : "決裁者と承認フローを確認しましょう",
      text.includes("KPI") || text.includes("目標") ? "KPIを提案サマリーで強調しましょう" : "問い合わせ数・応募数などの目標値を確認しましょう",
      text.includes("競合") ? "競合比較を具体化しましょう" : "競合サイトや比較対象を確認しましょう"
    ],
    nextFocus: ["最終決裁者", "予算上限", "公開希望時期", "競合比較", "公開後の運用体制"].filter((item) => !text.includes(item.slice(0, 2))).slice(0, 3)
  };
}

function buildNextMeetingPrep(form: ProposalRequest, missingItems: InfoCheck[]): NextMeetingPrep {
  return {
    confirmations: missingItems.slice(0, 5).map((item) => `${item.label}: ${item.nextQuestion}`),
    homework: [
      "競合サイトの導線・CTA・SEO観点を確認",
      "必須範囲とオプション範囲の見積を整理",
      "提案サマリーとKPI案を1枚で説明できるよう準備"
    ],
    deliverables: [
      "要約PowerPoint",
      "詳細PowerPoint",
      "概算見積書PDF",
      "次回確認事項リスト"
    ]
  };
}

function buildWinRateCoachAdvice(form: ProposalRequest, strategyCards: StrategyCard[]) {
  const text = allInputText(form);
  return {
    additions: [
      text.includes("KPI") ? "KPI達成までの改善サイクルを追加" : "問い合わせ数・応募数などのKPI目標を追加",
      "費用対効果と優先順位を1枚で説明",
      "次回確認事項を商談最後に合意"
    ],
    differentiation: [
      form.competitor_site_url || form.competitor_company_name ? "競合のCTA・コンテンツ量・SEOとの差を表で提示" : "競合サイトを確認して比較表を追加",
      strategyCards[0] ? `${strategyCards[0].title}を中心軸にする` : "実績訴求と運用支援を差別化軸にする",
      "公開後の改善運用まで含めて提案"
    ],
    delight: [
      "初回から要約版PPTと見積書PDFをセットで提示",
      "お客様側の社内説明に使いやすい1枚サマリーを追加",
      "CMS更新マニュアルや公開後30日改善プランを提案"
    ]
  };
}

function buildSalesDailyReport(form: ProposalRequest, evaluation: MeetingEvaluation): DailyReport {
  return {
    activities: ["Ready Crew案件の整理", "AIによる提案書初稿作成", "商談準備チェックと質問設計"],
    meeting: [`${extractClientName(form)}のWeb制作相談`, form.project_brief.trim().slice(0, 90) || "案件概要は要確認"],
    results: [`商談評価 ${evaluation.total}点`, `受注確率 ${deriveDealEvaluation(form, buildInfoChecks(form), deriveEstimateSummary(form)).probability}%`],
    issues: evaluation.improvements,
    tomorrow: ["不足情報の確認", "提案資料の最終調整", "次回商談日程の確認"]
  };
}

function buildBossReport(form: ProposalRequest, deal: DealEvaluation, missingItems: InfoCheck[]) {
  const report = `${extractClientName(form)}のWeb制作案件です。${form.project_brief.trim().slice(0, 90)}。受注確率は${deal.probability}%、判断は「${deal.decision}」。現在の課題は${missingItems.map((item) => item.label).slice(0, 3).join("、") || "大きな不足なし"}です。今後は不足情報確認、競合比較、概算見積の調整を行い、次回商談で提案内容を固めます。`;
  return report.slice(0, 300);
}

function classifyKnowledge(history: HistoryEntry[], form: ProposalRequest): KnowledgeGroups {
  const similar = buildSimilarCases(history, form).map((item) => item.entry);
  const success = history.filter((entry) => (entry.result.analysis.win_probability.probability ?? 0) >= 70).slice(0, 3);
  const lost = history.filter((entry) => (entry.result.analysis.win_probability.probability ?? 0) < 40).slice(0, 3);
  return { similar, success, lost };
}

function hasAny(text: string, patterns: (RegExp | string)[]) {
  return patterns.some((pattern) => (typeof pattern === "string" ? text.includes(pattern) : pattern.test(text)));
}

function buildInfoChecks(form: ProposalRequest): InfoCheck[] {
  const text = allInputText(form);
  const budgetIsClear = hasAny(text, [/予算\s*[:：]?\s*[0-9０-９]+/, /[0-9０-９]+\s*(万|万円)/]) && !/予算.*未定|未定.*予算/.test(text);

  return [
    {
      key: "budget",
      label: "予算",
      found: budgetIsClear,
      targetField: "見積条件 > 予算感",
      nextQuestion: "想定予算、上限、分割提案の可否"
    },
    {
      key: "deadline",
      label: "納期",
      found: hasAny(text, ["納期", "公開希望", "公開時期", "リリース", "9月", "10月", "急ぎ", "早め"]) && !/納期.*未定|公開.*未定/.test(text),
      targetField: "見積条件 > 公開希望時期",
      nextQuestion: "希望公開日、必達期限、社内確認に必要な期間"
    },
    {
      key: "decision-maker",
      label: "決裁者",
      found: hasAny(text, ["決裁", "決裁者", "代表", "社長", "役員", "部長", "責任者", "稟議", "承認"]),
      targetField: "案件概要 または 提案先企業情報",
      nextQuestion: "最終決裁者、選定関与者、稟議の流れ"
    },
    {
      key: "current-site",
      label: "既存サイトURL",
      found: hasAny(text, [/https?:\/\/\S+/, "既存サイトURL", "URL"]),
      targetField: "提案先企業情報",
      nextQuestion: "既存サイトURL、アクセス状況、改善したいページ"
    },
    {
      key: "cms",
      label: "CMS希望",
      found: hasAny(text, ["CMS", "WordPress", "ワードプレス", "更新", "運用"]),
      targetField: "見積条件 > CMS有無",
      nextQuestion: "CMS要否、更新担当者、更新頻度、承認フロー"
    },
    {
      key: "seo",
      label: "SEO希望",
      found: hasAny(text, ["SEO", "検索", "自然検索", "流入", "記事", "コンテンツマーケティング"]),
      targetField: "見積条件 > SEO対策有無",
      nextQuestion: "狙いたい検索キーワード、現状流入、SEO対象ページ"
    },
    {
      key: "competitor",
      label: "競合有無",
      found: Boolean(form.competitor_site_url.trim() || form.competitor_company_name.trim()) || hasAny(text, ["競合", "他社", "比較", "ベンチマーク", "差別化"]),
      targetField: "競合企業名・競合サイトURL",
      nextQuestion: "比較対象の競合サイト、勝ちたい訴求軸"
    }
  ];
}

function buildHearingSheet(form: ProposalRequest): HearingSheetCategory[] {
  const text = allInputText(form);
  const hasBusiness = hasAny(text, ["事業", "業種", "サービス", "商品", "商材", "不動産", "採用", "BtoB", "BtoC"]) || form.client_company_info.trim().length >= 20;
  const hasTarget = hasAny(text, ["ターゲット", "顧客", "ユーザー", "求職者", "法人", "個人", "購入者", "検討者", "ペルソナ"]);
  const hasCompetitor = Boolean(form.competitor_site_url.trim() || form.competitor_company_name.trim()) || hasAny(text, ["競合", "他社", "比較", "ベンチマーク", "差別化"]);
  const hasBudget = hasAny(text, [/予算\s*[:：]?\s*[0-9０-９]+/, /[0-9０-９]+\s*(万|万円)/]) && !/予算.*未定|未定.*予算/.test(text);
  const hasDeadline = hasAny(text, ["納期", "公開希望", "公開時期", "リリース", "9月", "10月", "急ぎ", "早め"]) && !/納期.*未定|公開.*未定/.test(text);
  const hasKpi = hasAny(text, ["KPI", "問い合わせ目標", "問合せ目標", "CV率", "コンバージョン", "アクセス数", "資料DL", "自然検索流入", "目標件数"]);
  const hasCms = hasAny(text, ["CMS", "WordPress", "ワードプレス", "更新機能"]) || Boolean(form.cms_required.trim());
  const hasOperation = hasAny(text, ["運用体制", "更新担当", "担当者", "保守", "月次", "レポート", "改善運用", "更新頻度"]);

  return [
    {
      key: "business",
      category: "事業内容",
      found: hasBusiness,
      summary: hasBusiness ? "事業・サービスの前提情報あり" : "事業内容、主力サービス、収益モデルが不足",
      questions: hasBusiness
        ? []
        : ["主力事業・主要サービスは何ですか？", "今回のWebサイトで最も訴求したい強みは何ですか？"]
    },
    {
      key: "target",
      category: "ターゲット",
      found: hasTarget,
      summary: hasTarget ? "想定ユーザーの記載あり" : "誰に向けたサイトかが不足",
      questions: hasTarget
        ? []
        : ["主なターゲットユーザーは誰ですか？", "問い合わせしてほしい顧客層や優先したい属性はありますか？"]
    },
    {
      key: "competitor",
      category: "競合",
      found: hasCompetitor,
      summary: hasCompetitor ? "競合・比較対象の情報あり" : "競合サイト・比較対象が不足",
      questions: hasCompetitor
        ? []
        : ["競合サイトはありますか？", "提案時に比較されやすい企業・サービスはありますか？"]
    },
    {
      key: "budget",
      category: "予算",
      found: hasBudget,
      summary: hasBudget ? "予算感の記載あり" : "予算感・上限・調整余地が不足",
      questions: hasBudget
        ? []
        : ["想定予算または上限予算はいくらですか？", "必須範囲とオプションに分けた提案は可能ですか？"]
    },
    {
      key: "deadline",
      category: "納期",
      found: hasDeadline,
      summary: hasDeadline ? "公開希望時期の記載あり" : "公開希望時期・必達期限が不足",
      questions: hasDeadline
        ? []
        : ["公開希望時期はいつですか？", "社内確認や素材準備に必要な期間はどの程度ですか？"]
    },
    {
      key: "kpi",
      category: "KPI",
      found: hasKpi,
      summary: hasKpi ? "成果指標の記載あり" : "問い合わせ数・CV率などの目標値が不足",
      questions: hasKpi
        ? []
        : ["年間の問い合わせ目標は？", "CV率、アクセス数、自然検索流入など重視するKPIは何ですか？"]
    },
    {
      key: "cms",
      category: "CMS",
      found: hasCms,
      summary: hasCms ? "CMS要否の記載あり" : "CMS要否・更新範囲が不足",
      questions: hasCms
        ? []
        : ["CMSは必要ですか？", "自社で更新したいページやコンテンツは何ですか？"]
    },
    {
      key: "operation",
      category: "運用体制",
      found: hasOperation,
      summary: hasOperation ? "運用・更新体制の記載あり" : "公開後の担当者・更新頻度が不足",
      questions: hasOperation
        ? []
        : ["公開後の更新担当者は誰ですか？", "公開後の保守、改善提案、レポート支援は必要ですか？"]
    }
  ];
}

function buildHearingSheetMarkdown(sheet: HearingSheetCategory[]) {
  const lines = sheet.map((item) => {
    const questions = item.questions.length
      ? item.questions.map((question) => `- Q. ${question}`).join("\n")
      : "- 入力情報あり。初回ヒアリングでは詳細条件を確認します。";
    return `### ${item.category}\n- 状態: ${item.found ? "入力情報あり" : "要ヒアリング"}\n- メモ: ${item.summary}\n${questions}`;
  });
  return `\n\n## ヒアリングシート\n\n${lines.join("\n\n")}`;
}

function buildExportMarkdown(markdown: string, form: ProposalRequest) {
  return `${markdown.trim()}${buildHearingSheetMarkdown(buildHearingSheet(form))}${buildHearingResultMarkdown(buildHearingResultSummary(form))}\n`;
}

function buildHearingResultSummary(form: ProposalRequest): HearingResultSummary {
  const rawLines = splitHearingResult(form.hearing_result);
  const hasInput = rawLines.length > 0;
  const unresolvedKeywords = [
    "未定",
    "未確認",
    "未決",
    "検討",
    "保留",
    "調整",
    "要相談",
    "確認中",
    "これから",
    "不明"
  ];
  if (!hasInput) {
    return {
      hasInput: false,
      minutes: ["ヒアリング結果を入力すると、議事録を自動生成します。"],
      decisions: ["ヒアリング結果入力後に抽出します。"],
      unresolved: ["ヒアリング結果入力後に抽出します。"],
      nextConfirmations: ["ヒアリング結果入力後に抽出します。"]
    };
  }

  const minutes = buildMeetingMinutes(rawLines);
  const decisions = pickHearingLines(rawLines, [
    "決定",
    "確定",
    "合意",
    "採用",
    "進める",
    "実施する",
    "依頼する",
    "WordPress",
    "CMSは",
    "公開は"
  ]).filter((line) => !hasAny(line, unresolvedKeywords));
  const unresolved = pickHearingLines(rawLines, unresolvedKeywords);
  const nextConfirmations = uniqueTextItems([
    ...pickHearingLines(rawLines, [
      "次回",
      "確認",
      "要確認",
      "宿題",
      "TODO",
      "誰",
      "いつ",
      "どの",
      "何",
      "ありますか",
      "ですか",
      "？",
      "?"
    ]),
    ...buildHearingSheet(form)
      .flatMap((item) => item.questions.map((question) => `${item.category}: ${question}`))
      .slice(0, 4)
  ]).slice(0, 5);

  return {
    hasInput,
    minutes: ensureSummaryItems(minutes, ["ヒアリング内容の要点を整理しました。"]),
    decisions: ensureSummaryItems(decisions, ["明確な決定事項は未抽出です。"]),
    unresolved: ensureSummaryItems(unresolved, ["大きな未決事項は未抽出です。"]),
    nextConfirmations: ensureSummaryItems(nextConfirmations, ["次回確認事項は未抽出です。"])
  };
}

function buildHearingResultMarkdown(summary: HearingResultSummary) {
  if (!summary.hasInput) {
    return "";
  }
  return `\n\n## ヒアリング結果整理\n\n### 議事録\n${markdownBullets(summary.minutes)}\n\n### 決定事項\n${markdownBullets(summary.decisions)}\n\n### 未決事項\n${markdownBullets(summary.unresolved)}\n\n### 次回確認事項\n${markdownBullets(summary.nextConfirmations)}`;
}

function splitHearingResult(value: string) {
  return value
    .split(/\r?\n|。|；|;/)
    .map((line) => line.replace(/^[・•\-\d０-９\s.．、]+/, "").trim())
    .filter(Boolean)
    .map((line) => trimText(line, 90));
}

function buildMeetingMinutes(lines: string[]) {
  const topics = [
    { label: "目的", patterns: ["目的", "ゴール", "問い合わせ", "採用", "リニューアル", "成果"] },
    { label: "対象", patterns: ["ターゲット", "顧客", "ユーザー", "求職者", "法人", "個人"] },
    { label: "要件", patterns: ["CMS", "フォーム", "SEO", "物件検索", "ページ", "機能"] },
    { label: "条件", patterns: ["予算", "納期", "公開", "スケジュール"] },
    { label: "体制", patterns: ["担当", "決裁", "運用", "更新", "承認"] }
  ];
  const picked = topics
    .map((topic) => {
      const line = lines.find((item) => hasAny(item, topic.patterns));
      return line ? `${topic.label}: ${line}` : "";
    })
    .filter(Boolean);
  return uniqueTextItems([...picked, ...lines]).slice(0, 6);
}

function pickHearingLines(lines: string[], keywords: string[]) {
  return uniqueTextItems(lines.filter((line) => hasAny(line, keywords))).slice(0, 5);
}

function uniqueTextItems(items: string[]) {
  return Array.from(new Set(items.map((item) => item.trim()).filter(Boolean)));
}

function ensureSummaryItems(items: string[], fallback: string[]) {
  return items.length ? items : fallback;
}

function trimText(value: string, maxLength: number) {
  return value.length <= maxLength ? value : `${value.slice(0, maxLength - 1)}…`;
}

function markdownBullets(items: string[]) {
  return items.map((item) => `- ${item}`).join("\n");
}

function deriveSalesIndicators(form: ProposalRequest): SalesIndicator[] {
  const text = allInputText(form);

  return [
    {
      title: "予算確度",
      ...deriveBudgetRank(text)
    },
    {
      title: "案件成熟度",
      ...deriveMaturityRank(text)
    }
  ];
}

function deriveBudgetRank(text: string): Omit<SalesIndicator, "title"> {
  if (/予算\s*[:：]?\s*[0-9０-９]+|[0-9０-９]+\s*(万|万円)/.test(text)) {
    return { rank: "A", label: "予算条件あり" };
  }
  if (text.includes("予算") && !/未定|未確認|これから/.test(text)) {
    return { rank: "B", label: "予算感あり" };
  }
  if (/予算.*未定|未定.*予算|予算未定/.test(text)) {
    return { rank: "C", label: "予算未定" };
  }
  return { rank: "D", label: "予算情報なし" };
}

function deriveMaturityRank(text: string): Omit<SalesIndicator, "title"> {
  const checks = [
    /問い合わせ|問合せ|CV|採用|SEO|CMS|リニューアル/.test(text),
    /予算|[0-9０-９]+\s*(万|万円)/.test(text),
    /納期|公開時期|公開希望|急ぎ|早め|リリース/.test(text),
    /決裁|代表|社長|責任者|稟議/.test(text),
    text.length >= 180
  ];
  const score = checks.filter(Boolean).length;
  if (score >= 4) return { rank: "A", label: "提案条件が具体的" };
  if (score === 3) return { rank: "B", label: "主要条件あり" };
  if (score === 2) return { rank: "C", label: "追加確認で具体化" };
  return { rank: "D", label: "初回確認を優先" };
}

function deriveCompetitorPoints(form: ProposalRequest): CompetitorPoint[] {
  const text = allInputText(form);
  const competitorName = form.competitor_company_name.trim() || "競合サイト";

  return [
    {
      label: "デザイン",
      point: `${competitorName}よりも第一印象、信頼感、問い合わせ導線の見つけやすさを強化`
    },
    {
      label: "SEO",
      point: hasAny(text, ["SEO", "検索", "自然検索"])
        ? "検索流入を獲得するページ構造とキーワード設計で差別化"
        : "主要サービス名・地域名・課題名での検索導線を設計"
    },
    {
      label: "導線設計",
      point: "比較検討から問い合わせまでのクリック数を減らし、CTAを明確化"
    },
    {
      label: "コンテンツ量",
      point: "サービス、実績、FAQ、導入事例を厚くして検討材料を増やす"
    },
    {
      label: "更新性",
      point: hasAny(text, ["CMS", "更新", "運用"])
        ? "CMSで実績・お知らせ・FAQを継続更新できる状態を作る"
        : "公開後に情報鮮度を維持できる更新領域を設計"
    },
    {
      label: "CTA",
      point: "ページ下部・実績・FAQから問い合わせへ自然につなげる"
    }
  ];
}

function deriveWinningStrategy(form: ProposalRequest) {
  const text = allInputText(form);
  if (hasAny(text, ["物件", "不動産", "賃貸", "売買"])) return "物件検索で勝つ";
  if (hasAny(text, ["SEO", "検索", "自然検索", "流入"])) return "SEOで勝つ";
  if (hasAny(text, ["実績", "事例", "導入"])) return "実績訴求で勝つ";
  if (hasAny(text, ["問い合わせ", "問合せ", "CV", "CTA"])) return "検索導線で勝つ";
  return "実績訴求とCTA改善で勝つ";
}

function normalizeNumberText(value: string) {
  return value
    .replace(/[０-９]/g, (char) => String.fromCharCode(char.charCodeAt(0) - 0xfee0))
    .replace(/[,，]/g, "");
}

function extractNumber(value: string) {
  const match = normalizeNumberText(value).match(/\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : null;
}

function extractBudgetAmount(value: string) {
  const normalized = normalizeNumberText(value);
  const matches = [...normalized.matchAll(/(\d+(?:\.\d+)?)\s*(万円|万|円)/g)];
  if (!matches.length) return null;

  const amounts = matches.map((match) => {
    const amount = Number(match[1]);
    return match[2] === "円" ? Math.round(amount / 10000) : amount;
  });
  return Math.max(...amounts);
}

function flagEnabled(value: string, text: string, fallbackPatterns: string[]) {
  const target = `${value}\n${text}`;
  if (hasAny(value, ["なし", "不要", "無", "無し", "なし想定"])) return false;
  if (hasAny(value, ["あり", "有", "必要", "希望", "対象", "実施", "要"])) return true;
  return hasAny(target, fallbackPatterns);
}

function formatEstimateRange(line: EstimateLine) {
  return line.enabled ? `${line.min}万〜${line.max}万円` : "対象外";
}

function deriveEstimateSummary(form: ProposalRequest): EstimateSummary {
  const text = allInputText(form);
  const pageCount =
    extractNumber(form.estimated_page_count) ??
    extractNumber(text.match(/\d+[ 　]*(ページ|頁|p)/i)?.[0] ?? "") ??
    10;
  const normalizedPageCount = Math.max(1, Math.min(60, Math.round(pageCount)));
  const pageBase = Math.max(8, normalizedPageCount);

  const hasCms = flagEnabled(form.cms_required, text, ["CMS", "WordPress", "更新"]);
  const hasForm = flagEnabled(form.contact_form_required, text, ["問い合わせフォーム", "問合せフォーム", "フォーム", "資料請求"]);
  const hasSpecial = flagEnabled(form.special_function_required, text, ["物件検索", "検索機能", "会員", "予約", "決済", "特殊機能"]);
  const hasSeo = flagEnabled(form.seo_required, text, ["SEO", "自然検索", "検索流入"]);
  const hasContent = flagEnabled(form.content_creation_required, text, ["撮影", "原稿", "ライティング", "取材"]);

  const lines: EstimateLine[] = [
    { name: "要件整理・ディレクション", min: normalizedPageCount > 15 ? 45 : 30, max: normalizedPageCount > 15 ? 75 : 50, priority: "必須対応", enabled: true },
    { name: "情報設計・ワイヤーフレーム", min: 25 + pageBase, max: 45 + pageBase * 2, priority: "必須対応", enabled: true },
    { name: "デザイン制作", min: 45 + pageBase * 4, max: 75 + pageBase * 7, priority: "必須対応", enabled: true },
    { name: "フロントエンド実装", min: 50 + pageBase * 5, max: 85 + pageBase * 8, priority: "必須対応", enabled: true },
    { name: "CMS構築", min: 50, max: 90, priority: "推奨対応", enabled: hasCms },
    { name: "フォーム実装", min: 15, max: 30, priority: "必須対応", enabled: hasForm },
    { name: "特殊機能開発", min: 80, max: 180, priority: "オプション対応", enabled: hasSpecial },
    { name: "SEO初期設計", min: 20, max: 40, priority: "推奨対応", enabled: hasSeo },
    { name: "撮影・原稿作成", min: 30, max: 80, priority: "オプション対応", enabled: hasContent },
    { name: "テスト・公開作業", min: 20, max: 35, priority: "必須対応", enabled: true },
    { name: "運用保守", min: 10, max: 20, priority: "オプション対応", enabled: true }
  ];

  const enabledLines = lines.filter((line) => line.enabled);
  const totalMin = enabledLines.reduce((sum, line) => sum + line.min, 0);
  const totalMax = enabledLines.reduce((sum, line) => sum + line.max, 0);
  const budgetAmount = extractBudgetAmount(`${form.budget_range}\n${text}`);
  const budgetFit =
    budgetAmount === null
      ? "予算未入力"
      : budgetAmount >= totalMax
        ? "予算内"
        : budgetAmount >= totalMin * 0.85
          ? "やや調整必要"
          : "予算超過の可能性あり";

  return {
    pageCount: normalizedPageCount,
    totalMin,
    totalMax,
    totalLabel: `${totalMin}万〜${totalMax}万円`,
    budgetAmount,
    budgetLabel: budgetAmount === null ? "未入力" : `${budgetAmount}万円`,
    budgetFit,
    lines,
    required: enabledLines.filter((line) => line.priority === "必須対応").map((line) => line.name),
    recommended: enabledLines.filter((line) => line.priority === "推奨対応").map((line) => line.name),
    optional: enabledLines.filter((line) => line.priority === "オプション対応").map((line) => line.name)
  };
}

function deriveDealEvaluation(form: ProposalRequest, checks: InfoCheck[], estimate: EstimateSummary): DealEvaluation {
  const text = allInputText(form);
  const foundCount = checks.filter((item) => item.found).length;
  let probability = 35 + foundCount * 7;
  const hasCompetitorInfo = Boolean(form.competitor_site_url.trim() || form.competitor_company_name.trim());

  const positives = [
    hasAny(text, ["問い合わせ", "問合せ", "CV"]) ? "成果目的が明確" : "",
    hasAny(text, ["リニューアル", "刷新", "改修"]) ? "制作ニーズが顕在化" : "",
    hasAny(text, ["CMS", "SEO", "採用"]) ? "提案余地が複数ある" : "",
    hasCompetitorInfo ? "競合比較を前提に勝ち筋を提示できる" : "",
    estimate.budgetFit === "予算内" ? "概算見積と予算感が合っている" : "",
    form.client_company_info.trim() ? "提案先情報あり" : "",
    form.case_studies.trim() ? "実績訴求に使える情報あり" : ""
  ].filter((item): item is string => Boolean(item));

  const negativeCandidates = checks
    .filter((item) => !item.found)
    .map(riskFactorFromCheck);
  if (hasCompetitorInfo) {
    negativeCandidates.push("競合有り");
  }
  if (estimate.budgetFit === "やや調整必要") {
    negativeCandidates.push("見積と予算に調整余地あり");
  }
  if (estimate.budgetFit === "予算超過の可能性あり") {
    negativeCandidates.push("見積が予算を超える可能性あり");
  }
  const negatives = prioritizeRiskFactors(negativeCandidates);

  probability += positives.length * 3;
  if (hasCompetitorInfo) probability += 4;
  if (estimate.budgetFit === "予算内") probability += 6;
  if (estimate.budgetFit === "やや調整必要") probability -= 6;
  if (estimate.budgetFit === "予算超過の可能性あり") probability -= 14;
  probability -= negatives.length * 4;
  probability = Math.max(20, Math.min(90, probability));

  const rank: Rank = probability >= 80 ? "A" : probability >= 60 ? "B" : probability >= 40 ? "C" : "D";
  const riskScore = deriveRiskScore(probability, negatives.length);
  const improvementActions = deriveImprovementActions(checks, estimate, hasCompetitorInfo);
  const projectedProbability = deriveProjectedProbability(probability, riskScore, improvementActions.length);
  const decision =
    probability >= 60 ? "提案推奨" : probability >= 40 ? "条件確認後に提案" : "見送り検討";
  const reason =
    probability >= 60
      ? "提案の目的が見えており、追加確認を行えば営業提案に進めます。"
      : probability >= 40
        ? "提案前に主要条件を補うことで、提案精度を高められます。"
        : "案件条件が薄いため、提案工数をかける前に一次確認を優先します。";

  return {
    rank,
    probability,
    riskScore,
    riskLabel: buildRiskLabel(riskScore),
    projectedProbability,
    decision,
    reason,
    positives: positives.length ? positives : ["案件概要の入力あり"],
    negatives: negatives.length ? negatives : ["大きな不足情報は少ない状態"],
    improvementActions
  };
}

function riskFactorFromCheck(item: InfoCheck) {
  const labels: Record<string, string> = {
    budget: "予算未確定",
    deadline: "納期未確認",
    "decision-maker": "決裁者未確認",
    "current-site": "既存サイトURL未確認",
    cms: "CMS希望未確認",
    seo: "SEO希望未確認",
    competitor: "競合未確認"
  };
  return labels[item.key] ?? `${item.label}未確認`;
}

function prioritizeRiskFactors(items: string[]) {
  const priority = ["予算", "納期", "競合", "決裁", "見積", "既存サイト", "CMS", "SEO"];
  const uniqueItems = Array.from(new Set(items.filter(Boolean)));
  return uniqueItems.sort((a, b) => {
    const aIndex = priority.findIndex((keyword) => a.includes(keyword));
    const bIndex = priority.findIndex((keyword) => b.includes(keyword));
    return (aIndex === -1 ? 99 : aIndex) - (bIndex === -1 ? 99 : bIndex);
  });
}

function deriveRiskScore(probability: number, riskCount: number) {
  let score = probability <= 25 ? 5 : probability <= 40 ? 4 : probability <= 60 ? 3 : probability <= 75 ? 2 : 1;
  if (riskCount >= 4) {
    score = Math.min(5, score + 1);
  }
  return score;
}

function buildRiskLabel(score: number) {
  const normalized = Math.max(1, Math.min(5, score));
  return `${"★".repeat(normalized)}${"☆".repeat(5 - normalized)}`;
}

function deriveProjectedProbability(probability: number, riskScore: number, actionCount: number) {
  let uplift = probability <= 25 ? 25 : probability <= 40 ? 20 : probability <= 60 ? 15 : 10;
  if (riskScore <= 2) {
    uplift = Math.min(uplift, 10);
  }
  if (actionCount < 3) {
    uplift = Math.max(8, uplift - 5);
  }
  return Math.min(90, probability + uplift);
}

function deriveImprovementActions(checks: InfoCheck[], estimate: EstimateSummary, hasCompetitorInfo: boolean) {
  const missingKeys = new Set(checks.filter((item) => !item.found).map((item) => item.key));
  const actions = [
    missingKeys.has("decision-maker") ? "決裁者確認" : "決裁プロセス確認",
    missingKeys.has("budget") || estimate.budgetFit === "やや調整必要" || estimate.budgetFit === "予算超過の可能性あり" ? "予算確認" : "",
    !hasCompetitorInfo || missingKeys.has("competitor") ? "競合ヒアリング" : "競合比較条件確認",
    missingKeys.has("deadline") ? "納期確認" : "",
    missingKeys.has("cms") ? "CMS要件確認" : "",
    missingKeys.has("seo") ? "SEO要件確認" : ""
  ].filter(Boolean);
  return Array.from(new Set(actions)).slice(0, 3);
}

function extractClientName(form: ProposalRequest, result?: AnalysisResponse | null) {
  const fromResult = result?.powerpoint_generation_data.client_name?.trim();
  if (fromResult && fromResult !== "提案先企業") {
    return fromResult;
  }
  const firstLine = form.client_company_info
    .split(/\r?\n/)
    .map((line) => line.trim())
    .find(Boolean);
  return firstLine || "提案先企業";
}

function buildInputSummary(form: ProposalRequest) {
  const brief = form.project_brief.trim().replace(/\s+/g, " ");
  return [
    { label: "提案先", value: extractClientName(form) },
    { label: "競合企業", value: form.competitor_company_name.trim() || "未入力" },
    { label: "競合サイトURL", value: form.competitor_site_url.trim() || "未入力" },
    { label: "想定ページ数", value: form.estimated_page_count.trim() || "未入力" },
    { label: "予算感", value: form.budget_range.trim() || "未入力" },
    { label: "公開希望時期", value: form.desired_launch_timing.trim() || "未入力" },
    { label: "案件概要", value: brief ? `${brief.slice(0, 96)}${brief.length > 96 ? "..." : ""}` : "未入力" },
    { label: "ヒアリング結果", value: form.hearing_result.trim() ? `${form.hearing_result.trim().slice(0, 96)}${form.hearing_result.trim().length > 96 ? "..." : ""}` : "未入力" },
    { label: "自社サービス", value: form.own_service_info.trim() || "未入力" },
    { label: "成功事例", value: form.case_studies.trim() || "未入力" }
  ];
}

function buildProposalPlan(
  form: ProposalRequest,
  checks: InfoCheck[],
  estimate: EstimateSummary,
  hearingQuestionCount: number
): ProposalPlan {
  const foundLabels = checks.filter((item) => item.found).map((item) => item.label);
  const missingLabels = checks.filter((item) => !item.found).map((item) => item.label);
  const competitorReady = Boolean(form.competitor_site_url.trim() || form.competitor_company_name.trim());

  return {
    inputInfo: [
      `入力済み情報: ${foundLabels.length ? foundLabels.join("、") : "案件概要のみ"}`,
      `不足情報: ${missingLabels.length ? missingLabels.join("、") : "大きな不足なし"}`,
      `競合情報: ${competitorReady ? "比較観点を生成可能" : "URLまたは企業名の入力待ち"}`,
      `概算見積: ${estimate.totalLabel} / ${estimate.budgetFit}`
    ],
    outputs: [
      "Markdownの提案書初稿",
      "通常版PowerPoint・要約PowerPoint",
      "見積書PDF",
      `次回ヒアリング質問 ${hearingQuestionCount}件`
    ],
    aiScope: [
      "案件概要から顧客理解・課題・提案方針を整理",
      "競合比較、見積、受注確率、ヒアリング項目を生成",
      "過去テンプレート・成功事例の入力内容を提案構成へ反映",
      "人間が確認しやすい初稿として出力"
    ],
    humanScope: [
      "提案先の固有名詞、実績、金額、納期の最終確認",
      "競合サイトの実画面確認と営業判断",
      "機密情報・顧客情報の取り扱い判断",
      "客先提出前の表現、法務、契約条件の確認"
    ]
  };
}

function buildBrowserUsePlan(form: ProposalRequest, competitorPoints: CompetitorPoint[]): BrowserUsePlan {
  const target = form.competitor_site_url.trim() || form.competitor_company_name.trim() || "競合サイトURL未入力";
  const hasTarget = target !== "競合サイトURL未入力";

  return {
    status: hasTarget ? "確認観点を生成済み" : "URL入力待ち",
    target,
    checks: competitorPoints.map((item) => `${item.label}: ${item.point}`),
    safety: [
      "公開ページの閲覧・比較観点生成に限定",
      "ログイン、フォーム送信、問い合わせ送信は行わない",
      "個人情報・認証情報・非公開情報は入力しない"
    ]
  };
}

function buildAutomationConcept(form: ProposalRequest, deal: DealEvaluation): ConceptBlock {
  const client = extractClientName(form);
  return {
    title: "Automations想定",
    label: "将来の自動確認機能",
    items: [
      "毎朝Ready Crew案件を確認し、新着案件を一覧化",
      "予算・納期・決裁者・競合情報が揃う案件を優先表示",
      `${client}のような高優先度案件は受注確率 ${deal.probability}% を目安に営業へ通知`,
      "今回は自動実行せず、画面上の企画表示に留める"
    ]
  };
}

function buildMcpConcept(form: ProposalRequest): ConceptBlock {
  const hasTemplate = Boolean(form.past_proposal_template.trim());
  const hasCases = Boolean(form.case_studies.trim());
  return {
    title: "MCP連携構想",
    label: "企画レベル",
    items: [
      `Google Drive: ${hasTemplate ? "入力済みテンプレートを提案構成に反映" : "過去提案書テンプレートの参照を想定"}`,
      `GitHub: ${hasCases ? "成功事例データを実績紹介に反映" : "実績情報・制作ナレッジの参照を想定"}`,
      "機密情報を扱う連携は、権限・保存範囲・共有先を確認してから実装",
      "今回は外部連携せず、入力済みテキストだけで生成"
    ]
  };
}

function buildOutputDigest(
  result: AnalysisResponse | null,
  estimate: EstimateSummary,
  form: ProposalRequest,
  missingItems: InfoCheck[],
  hearingSummary: HearingResultSummary
): OutputDigestSection[] {
  if (!result) {
    return [];
  }

  const analysis = result.analysis;
  const topIssues = analysis.issue_priorities.length
    ? analysis.issue_priorities.slice(0, 3).map((item) => `${item.issue}: ${item.proposed_response}`)
    : analysis.assumed_customer_issues.slice(0, 3).map((item) => item.issue);
  const nextItems = uniqueTextItems([
    ...missingItems.map((item) => `${item.targetField}: ${item.nextQuestion}`),
    ...hearingSummary.nextConfirmations
  ]).slice(0, 4);
  const schedule = form.desired_launch_timing.trim() || "公開希望時期は次回確認";

  return [
    {
      title: "提案要約",
      items: [analysis.project_summary, `受注確率: ${analysis.win_probability.probability ?? 0}% / ${analysis.win_probability.rank}ランク`]
    },
    {
      title: "顧客課題",
      items: topIssues.length ? topIssues : ["顧客課題はMarkdown本文で確認できます。"]
    },
    {
      title: "提案方針",
      items: [analysis.proposal_policy, analysis.proposal_story].filter(Boolean).slice(0, 2)
    },
    {
      title: "見積・スケジュール",
      items: [`概算見積: ${estimate.totalLabel}（${estimate.budgetFit}）`, `スケジュール: ${schedule}`]
    },
    {
      title: "次回確認事項",
      items: nextItems.length ? nextItems : ["客先提出前に固有名詞、金額、納期、実績表記を最終確認します。"]
    }
  ];
}

function buildErrorAdvice(message: string): ErrorAdvice {
  const normalized = message.toLowerCase();

  if (/401|403|ログイン|認証|password|unauthorized/.test(normalized)) {
    return {
      title: "認証エラー",
      cause: "ログイン期限切れ、パスワード誤り、またはBackend側のAPP_ACCESS_PASSWORD未設定の可能性があります。",
      action: "次の行動: 再ログイン / RenderのAPP_ACCESS_PASSWORDを確認 / Frontendを再読み込みする。",
      detail: message
    };
  }

  if (/ppt|powerpoint|pptx/.test(normalized)) {
    return {
      title: "PPTX生成失敗",
      cause: "PowerPoint生成処理、入力データ、またはBackend側の一時的な問題の可能性があります。",
      action: "次の行動: Backendログ確認 / 入力文字量を減らす / 再実行する。",
      detail: message
    };
  }

  if (/pdf|見積書/.test(normalized)) {
    return {
      title: "PDF生成失敗",
      cause: "PDF生成処理、見積データ、またはBackend側の一時的な問題の可能性があります。",
      action: "次の行動: Backendログ確認 / 提案書生成後に再度PDFを出力する。",
      detail: message
    };
  }

  if (/429|rate|レート|制限|quota|insufficient_quota/.test(normalized) || /API.*制限|上限/.test(message)) {
    return {
      title: "OpenAI API制限の可能性があります",
      cause: "短時間の利用回数、API利用上限、または請求設定により生成が止まった可能性があります。",
      action: "次の行動: 時間を置く / モックモードで試す / OpenAIの利用上限・請求設定・APIキーを確認する。",
      detail: message
    };
  }

  if (/400|422|入力|不足|min_length|validation|短く/.test(normalized) || /入力|不足/.test(message)) {
    return {
      title: "入力内容を確認してください",
      cause: "案件概要が短い、必須項目が不足している、または送信形式が想定と異なる可能性があります。",
      action: "次の行動: 不足項目を確認 / 案件メールを貼り直す / 確認画面からこのまま生成する。",
      detail: message
    };
  }

  if (/failed to fetch|network|通信|接続|cors|502|503|504|timeout|タイムアウト/.test(normalized) || /通信|接続|タイムアウト|CORS/.test(message)) {
    return {
      title: "通信エラーの可能性があります",
      cause: "FrontendからBackendへ接続できていない、Backendが停止している、またはCORS設定が合っていない可能性があります。",
      action: "次の行動: 再読み込み / Backend確認 / NEXT_PUBLIC_API_URLとCORS設定を確認する。",
      detail: message
    };
  }

  return {
    title: "生成中にエラーが発生しました",
    cause: "一時的なAPIエラー、入力内容、またはBackendログで確認できる問題の可能性があります。",
    action: "次の行動: 再実行 / 入力内容を確認 / 解消しない場合はBackendログを確認する。",
    detail: message
  };
}

function extractProbability(winProbability?: WinProbability, fallback = 0) {
  if (typeof winProbability?.probability === "number" && winProbability.probability > 0) {
    return winProbability.probability;
  }
  const label = winProbability?.label ?? "";
  const match = label.match(/(\d{1,3})\s*%/);
  if (match) {
    return Number(match[1]);
  }
  return fallback;
}

function buildDisplayedWinProbability(winProbability: WinProbability | undefined, fallback: DealEvaluation) {
  const probability = extractProbability(winProbability, fallback.probability);
  const riskScore = Math.max(
    1,
    Math.min(5, winProbability?.risk_score ?? deriveRiskScore(probability, winProbability?.risk_factors?.length ?? fallback.negatives.length))
  );
  const projectedProbability =
    winProbability?.projected_probability_after_actions && winProbability.projected_probability_after_actions > probability
      ? winProbability.projected_probability_after_actions
      : deriveProjectedProbability(probability, riskScore, fallback.improvementActions.length);

  return {
    rank: winProbability?.rank ?? fallback.rank,
    label: winProbability?.label ?? `${fallback.rank}ランク`,
    reason: winProbability?.reason ?? fallback.reason,
    probability,
    riskScore,
    riskLabel: winProbability?.risk_label || buildRiskLabel(riskScore),
    projectedProbability,
    positives: winProbability?.positive_factors?.length ? winProbability.positive_factors : fallback.positives,
    riskFactors: winProbability?.risk_factors?.length ? winProbability.risk_factors : fallback.negatives,
    improvementActions: winProbability?.improvement_actions?.length
      ? winProbability.improvement_actions
      : fallback.improvementActions
  };
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ja-JP", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function safeHistoryParse(value: string | null): HistoryEntry[] {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value) as HistoryEntry[];
    if (!Array.isArray(parsed)) return [];
    return parsed.map((entry) => ({
      ...entry,
      form: normalizeForm(entry.form)
    }));
  } catch {
    return [];
  }
}

function normalizeForm(value: Partial<ProposalRequest> | undefined): ProposalRequest {
  return {
    ...initialForm,
    ...(value ?? {})
  };
}

function downloadTextFile(content: string, filename: string, type = "text/markdown;charset=utf-8") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function sanitizeFileName(value: string) {
  return value.replace(/[\\/:*?"<>|]/g, "-").replace(/\s+/g, " ").trim().slice(0, 80);
}

function splitBusinessLines(value: string, fallback: string[] = []) {
  const lines = value
    .split(/\r?\n|。|;|；/)
    .map((line) => line.replace(/^[-・\s]+/, "").trim())
    .filter((line) => line.length >= 3);
  return uniqueTextItems(lines.length ? lines : fallback);
}

function pickBusinessItems(value: string, keywords: string[], fallback: string[], limit = 4) {
  const lines = splitBusinessLines(value);
  const matched = lines.filter((line) => keywords.some((keyword) => line.includes(keyword)));
  return uniqueTextItems([...(matched.length ? matched : lines), ...fallback]).slice(0, limit);
}

function buildInternalMinutes(input: string): MinutesAiResult {
  const text = input.trim();
  const lines = splitBusinessLines(text, ["会議内容を確認し、目的・課題・決定事項・次回アクションを整理します。"]);
  const decisions = pickBusinessItems(text, ["決定", "合意", "進め", "対応", "採用"], ["提案方針と次回確認事項を整理して進行します。"], 3);
  const unresolved = pickBusinessItems(text, ["未定", "確認", "課題", "懸念", "不足"], ["予算、納期、決裁者、運用体制の未確定項目を確認します。"], 4);
  const todoSources = pickBusinessItems(text, ["対応", "作成", "確認", "送付", "共有", "準備"], lines, 5);
  return {
    minutes: lines.slice(0, 5),
    decisions,
    unresolved,
    todos: todoSources.slice(0, 5).map((task, index) => ({
      task,
      owner: index === 0 ? "営業担当" : "担当者確認",
      deadline: task.includes("至急") || task.includes("今週") ? "今週中" : "次回商談前"
    })),
    nextConfirmations: unresolved.slice(0, 4)
  };
}

function buildInternalMail(purpose: string, recipient: string, content: string, tone: string): MailAiResult {
  const target = recipient.trim() || "ご担当者様";
  const mailPurpose = purpose.trim() || "提案内容のご案内";
  const bodyItems = splitBusinessLines(content, ["ご相談内容を踏まえ、提案資料の初稿を準備しました。"]);
  const selectedTone = tone.trim() || "丁寧";
  const body = `${target}\n\nいつもお世話になっております。\n${mailPurpose}についてご連絡いたします。\n\n${bodyItems
    .slice(0, 4)
    .map((item) => `・${item}`)
    .join("\n")}\n\nご確認いただき、ご不明点や追加で確認したい点がありましたらお知らせください。\n引き続きよろしくお願いいたします。\n\n署名`;
  return {
    subject: `【ご確認】${mailPurpose}`,
    body,
    reply: `${target}\n\nご返信ありがとうございます。いただいた内容を踏まえて、提案内容と見積条件を更新いたします。\n次回までに確認事項を整理してお送りします。`,
    polite: `${target}\n\n平素より大変お世話になっております。\n${mailPurpose}につきまして、下記の通りご案内申し上げます。\n\n${bodyItems.slice(0, 3).join("\n")}\n\nお忙しいところ恐れ入りますが、ご確認のほどよろしくお願いいたします。`,
    short: `${target}\n\n${mailPurpose}の件、要点を共有いたします。\n${bodyItems.slice(0, 3).map((item) => `・${item}`).join("\n")}\n\nご確認をお願いいたします。${selectedTone ? `\n\nトーン: ${selectedTone}` : ""}`
  };
}

function buildInternalTasks(input: string): TaskAiResult {
  const items = splitBusinessLines(input, ["案件内容を確認し、次にやることを整理します。"]).slice(0, 6);
  const priorities = ["高", "高", "中", "中", "低", "低"];
  return {
    tasks: items.map((item, index) => ({
      task: item,
      priority: priorities[index] ?? "中",
      owner: item.includes("顧客") || item.includes("お客様") ? "営業担当" : "担当者確認",
      deadline: item.includes("納期") || item.includes("公開") ? "日程確認後" : "次回確認まで",
      risk: item.includes("未定") || item.includes("確認") ? "未確定のまま進むと手戻りが発生" : "対応漏れに注意"
    })),
    nextAction: "優先度が高い項目から、担当者と期限を確定します。"
  };
}

function buildInternalFaq(question: string): FaqAiResult {
  const q = question.trim() || "社内ルールや過去資料の確認事項";
  const department = q.includes("見積") || q.includes("請求") ? "経理・営業管理" : q.includes("契約") ? "法務・管理部" : "担当部署";
  return {
    answer: `${q}については、現時点の入力情報をもとに一次回答を作成します。正式回答は担当部署の確認後に共有します。`,
    department,
    references: ["過去提案書テンプレート", "社内制作フロー", "見積ルール", "案件管理シート"],
    notes: [
      "現時点では外部DBへ接続せず、入力文から回答案を作成します。",
      "Google Driveや社内FAQ/RAGは今後MCPで連携予定です。",
      "顧客名、金額、契約条件は社外共有前に人が確認します。"
    ]
  };
}

function buildInternalSummary(input: string): SummaryAiResult {
  const lines = splitBusinessLines(input, ["資料内容を確認し、要点・アクション・リスクを整理します。"]);
  return {
    threeLines: uniqueTextItems(lines).slice(0, 3),
    points: pickBusinessItems(input, ["目的", "課題", "提案", "重要", "方針"], lines, 5),
    actions: pickBusinessItems(input, ["対応", "作成", "確認", "送付", "実施"], ["次回までに不足情報を確認します。"], 4),
    risks: pickBusinessItems(input, ["懸念", "リスク", "未定", "不足", "遅延"], ["予算、納期、担当者が未確定の場合は進行リスクになります。"], 4),
    bossSummary: `${lines.slice(0, 3).join("。")}。次回までに重要事項を確認し、提案内容へ反映します。`
  };
}

function buildInternalReport(input: string): ReportAiResult {
  const lines = splitBusinessLines(input, ["本日の活動内容を整理します。"]);
  const actions = pickBusinessItems(input, ["商談", "提案", "確認", "作成", "連絡"], lines, 4);
  const issues = pickBusinessItems(input, ["課題", "未定", "不足", "懸念"], ["未確定項目を次回確認します。"], 3);
  return {
    daily: actions,
    weekly: uniqueTextItems([...actions, "提案準備と顧客確認事項の整理を進めました。"]).slice(0, 5),
    results: pickBusinessItems(input, ["完了", "成果", "作成", "送付"], ["提案準備の初稿を作成しました。"], 3),
    issues,
    tomorrow: ["不足情報の確認", "提案資料の更新", "次回商談に向けた質問準備"],
    bossMessage: `本日は${actions[0] ?? "案件対応"}を進めました。課題は${issues[0] ?? "未確定項目の確認"}です。明日は不足情報の確認と提案資料の更新を進めます。`
  };
}

function extractDomainLabel(url: string) {
  try {
    const parsed = new URL(url.startsWith("http") ? url : `https://${url}`);
    return parsed.hostname.replace(/^www\./, "");
  } catch {
    return url.trim() || "会社URL未入力";
  }
}

function buildCompanyResearch(url: string, form: ProposalRequest, extractedInfo: ExtractedInfo | null): CompanyResearch {
  const domain = extractDomainLabel(url);
  const allText = allInputText(form);
  const clientName = extractClientName(form);
  const competitor = form.competitor_company_name.trim() || extractedInfo?.competitor || "同業・地域競合";
  const hasRecruit = /採用|求人|人材|応募|社員/i.test(allText);
  const hasSeo = /SEO|検索|自然流入|流入|地域名/i.test(allText);
  const hasCms = /CMS|WordPress|更新|お知らせ/i.test(allText);

  return {
    overview: `${clientName === "提案先企業" ? domain : clientName}の公開情報、案件概要、既存サイトURLをもとに、事業内容・顧客接点・改善余地を確認します。`,
    competitors: uniqueTextItems([competitor, form.competitor_site_url.trim(), "検索結果上位の同業サイト", "採用・サービス訴求で比較される企業"]).slice(0, 4),
    recruitment: hasRecruit ? "採用情報の訴求、社員紹介、応募導線を重点確認します。" : "採用情報は未入力です。会社理解と信頼形成の補助情報として確認します。",
    news: uniqueTextItems([
      "直近のお知らせ更新頻度",
      "新サービス・店舗・採用に関する発信",
      hasCms ? "CMSで継続更新できるニュース設計" : "更新停止がないか確認"
    ]).slice(0, 4),
    services: uniqueTextItems([
      form.project_brief.includes("物件") ? "物件検索・問い合わせ導線" : "主力サービスの見せ方",
      form.project_brief.includes("採用") ? "採用コンテンツ" : "サービス紹介",
      hasSeo ? "SEO記事・FAQ・地域ページ" : "FAQ・実績・導入事例"
    ]),
    sns: ["X / Instagram / Facebook / LinkedInの有無", "更新頻度", "サイト導線との接続", "採用・実績訴求への活用"]
  };
}

function buildRoleGuidance(role: AiEmployeeRole, form: ProposalRequest, estimate: EstimateSummary) {
  const roleLabel = aiEmployeeRoles.find((item) => item.key === role)?.label ?? "AI社員";
  const base = {
    secretary: ["次回確認事項、日程、送付メールを先に整えます。", "未入力項目を確認リスト化し、営業担当の抜け漏れを減らします。"],
    sales: ["受注確率、競合差別化、提案ストーリーを強化します。", "顧客が社内説明しやすい要約PowerPointを優先します。"],
    director: ["要件、サイトマップ、制作範囲、体制を具体化します。", "CMS、SEO、運用保守の前提条件を提案に反映します。"],
    writer: ["提案サマリー、メール、顧客課題の言葉を磨きます。", "AIっぽい曖昧表現を減らし、営業が話しやすい表現に整えます。"],
    designer: ["PowerPointの見せ方、導線図、KPI、比較表の視認性を確認します。", "顧客の信頼感が伝わる清潔な資料構成に寄せます。"],
    pm: ["見積、スケジュール、リスク、担当者を整理します。", `概算見積は${estimate.totalLabel}を前提に、必須・推奨・オプションを分けます。`]
  } satisfies Record<AiEmployeeRole, string[]>;

  return {
    title: `${roleLabel}として提案を支援`,
    items: uniqueTextItems([...base[role], form.budget_range ? `予算感「${form.budget_range}」との整合性を確認します。` : "予算未入力の場合は次回確認事項に入れます。"]).slice(0, 4)
  };
}

function buildAiCoworkerReviews(role: AiEmployeeRole, form: ProposalRequest, estimate: EstimateSummary) {
  const roleGuidance = buildRoleGuidance(role, form, estimate);
  return [
    { reviewer: "営業AI", comment: "顧客課題、受注確率、競合差別化を先に伝える構成にします。", improvement: roleGuidance.items[0] },
    { reviewer: "PM AI", comment: "予算、納期、体制、リスクを見積条件と合わせて明確化します。", improvement: `概算見積 ${estimate.totalLabel} の前提条件を資料内に残します。` },
    { reviewer: "デザイナーAI", comment: "情報量の多いスライドはカード、表、ステップ図に分けて読みやすくします。", improvement: "顧客が30秒で理解できるサマリーとKPIを強調します。" },
    { reviewer: "社長AI", comment: "提案が売上・採用・問い合わせ改善にどう効くかを経営目線で補強します。", improvement: "投資対効果と次回アクションを最後に明確化します。" }
  ];
}

export default function Home() {
  const [activeMode, setActiveMode] = useState<WorkMode>("sales");
  const [modeUsageCounts, setModeUsageCounts] = useState<GeneratedCounts>(initialModeCounts);
  const [recentFeatures, setRecentFeatures] = useState<string[]>([]);
  const [selectedAiEmployee, setSelectedAiEmployee] = useState<AiEmployeeRole>("sales");
  const [companyResearch, setCompanyResearch] = useState<CompanyResearch | null>(null);
  const [agentSteps, setAgentSteps] = useState<DigitalAgentStep[]>(initialAgentSteps);
  const [isAgentRunning, setIsAgentRunning] = useState(false);
  const [automationSettings, setAutomationSettings] = useState<AutomationSettings>({
    morning: false,
    weekly: false,
    deadline: false
  });
  const [form, setForm] = useState<ProposalRequest>(initialForm);
  const [inputMode, setInputMode] = useState<InputMode>("easy");
  const [easyInput, setEasyInput] = useState<EasyInput>(initialEasyInput);
  const [minimalInput, setMinimalInput] = useState<MinimalInput>(initialMinimalInput);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>(initialChatMessages);
  const [chatAnswers, setChatAnswers] = useState<ChatAnswers>({});
  const [chatQuestionIndex, setChatQuestionIndex] = useState(0);
  const [chatDraft, setChatDraft] = useState("");
  const [rawSourceText, setRawSourceText] = useState("");
  const [companyHomeUrl, setCompanyHomeUrl] = useState("");
  const [extractedInfo, setExtractedInfo] = useState<ExtractedInfo | null>(null);
  const [urlInsight, setUrlInsight] = useState<UrlInsight | null>(null);
  const [assistantQuestionCount, setAssistantQuestionCount] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [editablePreviewSlides, setEditablePreviewSlides] = useState<PreviewSlide[]>([]);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [showEmailDraft, setShowEmailDraft] = useState(false);
  const [showMinutes, setShowMinutes] = useState(false);
  const [liveMeetingMemo, setLiveMeetingMemo] = useState("");
  const [dailyReport, setDailyReport] = useState<DailyReport | null>(null);
  const [bossReport, setBossReport] = useState("");
  const [roleplayScenario, setRoleplayScenario] = useState<RoleplayScenario>("recruit");
  const [roleplayMessages, setRoleplayMessages] = useState<RoleplayMessage[]>([]);
  const [roleplayDraft, setRoleplayDraft] = useState("");
  const [roleplayFinished, setRoleplayFinished] = useState(false);
  const [minutesInput, setMinutesInput] = useState("");
  const [minutesResult, setMinutesResult] = useState<MinutesAiResult | null>(null);
  const [mailPurpose, setMailPurpose] = useState("");
  const [mailRecipient, setMailRecipient] = useState("");
  const [mailContent, setMailContent] = useState("");
  const [mailTone, setMailTone] = useState("丁寧");
  const [mailResult, setMailResult] = useState<MailAiResult | null>(null);
  const [taskInput, setTaskInput] = useState("");
  const [taskResult, setTaskResult] = useState<TaskAiResult | null>(null);
  const [faqQuestion, setFaqQuestion] = useState("");
  const [faqResult, setFaqResult] = useState<FaqAiResult | null>(null);
  const [summaryInput, setSummaryInput] = useState("");
  const [summaryResult, setSummaryResult] = useState<SummaryAiResult | null>(null);
  const [reportInput, setReportInput] = useState("");
  const [reportResult, setReportResult] = useState<ReportAiResult | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isDownloadingPowerPoint, setIsDownloadingPowerPoint] = useState(false);
  const [isDownloadingSummaryPowerPoint, setIsDownloadingSummaryPowerPoint] = useState(false);
  const [isDownloadingEstimatePdf, setIsDownloadingEstimatePdf] = useState(false);
  const [error, setError] = useState("");
  const [lastDownloadRetry, setLastDownloadRetry] = useState<"pptx" | "summary-pptx" | "estimate-pdf" | null>(null);
  const [copyState, setCopyState] = useState<"idle" | "copied">("idle");
  const [healthSnapshot, setHealthSnapshot] = useState<HealthSnapshot | null>(null);
  const [usageLogs, setUsageLogs] = useState<UsageLogEntry[]>([]);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [managedUsers, setManagedUsers] = useState<ManagedUser[]>([]);
  const [crmCustomers, setCrmCustomers] = useState<CrmCustomer[]>([]);
  const [crmProjects, setCrmProjects] = useState<CrmProject[]>([]);
  const [dbLogCount, setDbLogCount] = useState(0);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);

  useEffect(() => {
    setHistory(safeHistoryParse(window.localStorage.getItem(HISTORY_KEY)));
    setUsageLogs(readUsageLogs());
    void refreshAccountData();
    const handler = () => void refreshAccountData();
    window.addEventListener("ready-crew-auth-changed", handler);
    return () => window.removeEventListener("ready-crew-auth-changed", handler);
  }, []);

  async function refreshAccountData() {
    const storedUser = getStoredUser();
    setCurrentUser(storedUser);
    if (!storedUser) return;
    try {
      const crm = await getCrm();
      setCrmCustomers(crm.customers);
      setCrmProjects(crm.projects);
    } catch {
      setCrmCustomers([]);
      setCrmProjects([]);
    }
    try {
      const logs = await getDbLogs();
      setDbLogCount(logs.logs.length);
    } catch {
      setDbLogCount(0);
    }
    if (storedUser.role === "admin") {
      try {
        const users = await listUsers();
        setManagedUsers(users.users);
      } catch {
        setManagedUsers([]);
      }
      try {
        const audit = await getAuditLogs();
        setAuditLogs(audit.logs);
      } catch {
        setAuditLogs([]);
      }
    }
  }

  const canSubmit = useMemo(() => {
    return form.project_brief.trim().length >= 20 && !isLoading;
  }, [form.project_brief, isLoading]);
  const canGenerate = currentUser?.role === "admin" || currentUser?.role === "member";

  const easyMissingItems = useMemo(() => buildEasyMissingItems(easyInput), [easyInput]);
  const canOrganizeEasyInput = easyMissingItems.length === 0;
  const chatReadiness = useMemo(() => buildChatReadiness(chatAnswers), [chatAnswers]);
  const infoChecks = useMemo(() => buildInfoChecks(form), [form]);
  const missingItems = useMemo(() => infoChecks.filter((item) => !item.found), [infoChecks]);
  const liveProjectSummary = useMemo(() => buildLiveProjectSummary(form, missingItems), [form, missingItems]);
  const salesOpportunityScore = useMemo(() => buildSalesOpportunityScore(form, infoChecks), [form, infoChecks]);
  const hearingSheet = useMemo(() => buildHearingSheet(form), [form]);
  const hearingQuestionCount = useMemo(
    () => hearingSheet.reduce((count, item) => count + item.questions.length, 0),
    [hearingSheet]
  );
  const hearingResultSummary = useMemo(() => buildHearingResultSummary(form), [form]);
  const salesIndicators = useMemo(() => deriveSalesIndicators(form), [form]);
  const estimateSummary = useMemo(() => deriveEstimateSummary(form), [form]);
  const dealEvaluation = useMemo(() => deriveDealEvaluation(form, infoChecks, estimateSummary), [form, infoChecks, estimateSummary]);
  const aiEmployeeGuidance = useMemo(
    () => buildRoleGuidance(selectedAiEmployee, form, estimateSummary),
    [selectedAiEmployee, form, estimateSummary]
  );
  const aiCoworkerReviews = useMemo(
    () => buildAiCoworkerReviews(selectedAiEmployee, form, estimateSummary),
    [selectedAiEmployee, form, estimateSummary]
  );
  const competitorPoints = useMemo(() => deriveCompetitorPoints(form), [form]);
  const winningStrategy = useMemo(() => deriveWinningStrategy(form), [form]);
  const proposalPlan = useMemo(
    () => buildProposalPlan(form, infoChecks, estimateSummary, hearingQuestionCount),
    [form, infoChecks, estimateSummary, hearingQuestionCount]
  );
  const browserUsePlan = useMemo(() => buildBrowserUsePlan(form, competitorPoints), [form, competitorPoints]);
  const automationConcept = useMemo(() => buildAutomationConcept(form, dealEvaluation), [form, dealEvaluation]);
  const mcpConcept = useMemo(() => buildMcpConcept(form), [form]);
  const aiRecommendations = useMemo(() => buildAiRecommendations(form, urlInsight), [form, urlInsight]);
  const strategyCards = useMemo(() => buildStrategyCards(form, aiRecommendations), [form, aiRecommendations]);
  const defaultPreviewSlides = useMemo(
    () => buildPreviewSlides(form, strategyCards, estimateSummary),
    [form, strategyCards, estimateSummary]
  );
  useEffect(() => {
    setEditablePreviewSlides(defaultPreviewSlides);
  }, [defaultPreviewSlides]);
  const preGenerateCards = useMemo(() => {
    const brief = form.project_brief.trim().replace(/\s+/g, " ");
    const purposes = extractedInfo?.purposes.length ? extractedInfo.purposes.join("、") : extractPurposeList(allInputText(form)).join("、");
    return [
      { label: "会社名", value: extractClientName(form) },
      { label: "案件内容", value: extractedInfo?.projectContent || (brief ? `${brief.slice(0, 110)}${brief.length > 110 ? "..." : ""}` : "Webサイト制作・改善提案") },
      { label: "目的", value: purposes || "問い合わせ獲得・信頼感向上を仮説として整理" },
      { label: "予算", value: form.budget_range.trim() || "未定" },
      { label: "納期", value: form.desired_launch_timing.trim() || "要確認" },
      { label: "競合", value: form.competitor_site_url.trim() || form.competitor_company_name.trim() || "競合未確認" },
      { label: "不足情報", value: missingItems.length ? missingItems.map((item) => item.label).join("、") : "大きな不足なし" }
    ];
  }, [extractedInfo, form, missingItems]);
  const displayedWin = useMemo(
    () => buildDisplayedWinProbability(result?.analysis.win_probability, dealEvaluation),
    [result?.analysis.win_probability, dealEvaluation]
  );
  const outputDigest = useMemo(
    () => buildOutputDigest(result, estimateSummary, form, missingItems, hearingResultSummary),
    [result, estimateSummary, form, missingItems, hearingResultSummary]
  );
  const displayedProbability = displayedWin.probability;
  const displayedMarkdown = useMemo(
    () => (result?.markdown ? buildExportMarkdown(result.markdown, form) : ""),
    [result?.markdown, form]
  );
  const qualityScore = useMemo(
    () => buildQualityScore(result, form, dealEvaluation, estimateSummary, strategyCards),
    [result, form, dealEvaluation, estimateSummary, strategyCards]
  );
  const draftEmail = useMemo(() => buildDraftEmail(form), [form]);
  const aiMinutes = useMemo(() => buildAiMinutes(form, extractedInfo), [form, extractedInfo]);
  const winRateImprovements = useMemo(() => buildWinRateImprovements(dealEvaluation, qualityScore), [dealEvaluation, qualityScore]);
  const similarCases = useMemo(() => buildSimilarCases(history, form), [history, form]);
  const dashboardMetrics = useMemo(() => buildDashboardMetrics(history, result), [history, result]);
  const monthlyDashboardMetrics = useMemo(
    () => buildMonthlyDashboardMetrics(history, result, qualityScore, dealEvaluation),
    [history, result, qualityScore, dealEvaluation]
  );
  const operationDashboardMetrics = useMemo(() => {
    const total = Object.values(modeUsageCounts).reduce((sum, count) => sum + count, 0);
    const savedMinutes = total * 45;
    return [
      { label: "今日の生成数", value: `${total}件`, note: "この画面で作成したAI出力" },
      { label: "営業提案数", value: `${modeUsageCounts.sales}件`, note: "提案書・PPT・見積につながる出力" },
      { label: "議事録生成数", value: `${modeUsageCounts.minutes}件`, note: "会議メモから整理" },
      { label: "メール作成数", value: `${modeUsageCounts.mail}件`, note: "件名・本文・返信案" },
      { label: "タスク整理数", value: `${modeUsageCounts.tasks}件`, note: "依頼や議事録から分解" },
      { label: "AI削減時間", value: `${savedMinutes}分`, note: "1件45分削減として概算" }
    ];
  }, [modeUsageCounts]);
  const preMeetingChecklist = useMemo(() => buildPreMeetingChecklist(infoChecks), [infoChecks]);
  const coachQuestions = useMemo(() => buildCoachQuestions(form, missingItems), [form, missingItems]);
  const realtimeQuestion = useMemo(() => buildRealtimeQuestion(liveMeetingMemo, coachQuestions), [liveMeetingMemo, coachQuestions]);
  const meetingEvaluation = useMemo(() => buildMeetingEvaluation(liveMeetingMemo || form.hearing_result, form), [liveMeetingMemo, form]);
  const nextMeetingPrep = useMemo(() => buildNextMeetingPrep(form, missingItems), [form, missingItems]);
  const winRateCoachAdvice = useMemo(() => buildWinRateCoachAdvice(form, strategyCards), [form, strategyCards]);
  const knowledgeGroups = useMemo(() => classifyKnowledge(history, form), [history, form]);
  const errorAdvice = useMemo(() => (error ? buildErrorAdvice(error) : null), [error]);
  const currentChatQuestion = chatQuestionFlow[Math.min(chatQuestionIndex, chatQuestionFlow.length - 1)];

  function recordModeUsage(mode: WorkMode) {
    const label = workModeTabs.find((item) => item.key === mode)?.label ?? mode;
    setModeUsageCounts((current) => ({ ...current, [mode]: current[mode] + 1 }));
    setRecentFeatures((current) => [label, ...current.filter((item) => item !== label)].slice(0, 5));
  }

  function recordUsage(featureName: string, inputLength: number, outputType: string, status: "success" | "failure", errorType = "") {
    appendUsageLog({
      featureName,
      inputLength,
      outputType,
      status,
      errorType
    });
    void saveUsageLogToBackend({
      feature_name: featureName,
      input_length: inputLength,
      output_type: outputType,
      status,
      error_type: errorType
    }).catch(() => undefined);
    setUsageLogs(readUsageLogs());
  }

  async function handleCreateUser(payload: { email: string; password: string; role: "admin" | "member" | "viewer" }) {
    await createUser(payload);
    const users = await listUsers();
    setManagedUsers(users.users);
  }

  async function handleToggleUser(userId: number, isActive: boolean) {
    await updateUserActive(userId, isActive);
    const users = await listUsers();
    setManagedUsers(users.users);
  }

  async function runCompanyResearch() {
    if (!companyHomeUrl.trim() && !form.client_company_info.trim() && !rawSourceText.trim()) {
      setError("会社URL、案件メール、または提案先企業情報を入力すると会社調査を開始できます。");
      return;
    }
    if (companyHomeUrl.trim()) {
      try {
        const research = await researchCompanyUrl({
          url: companyHomeUrl,
          project_brief: form.project_brief,
          client_company_info: form.client_company_info
        });
        setCompanyResearch(research);
        setError("");
        recordUsage("会社URL調査", companyHomeUrl.length + form.project_brief.length, "company-research", "success");
        return;
      } catch {
        setCompanyResearch(buildCompanyResearch(companyHomeUrl, form, extractedInfo));
        setError("会社URLの公開ページ取得に失敗したため、入力情報から調査観点を整理しました。");
        recordUsage("会社URL調査", companyHomeUrl.length + form.project_brief.length, "company-research", "failure", "通信エラー");
        return;
      }
    }
    setCompanyResearch(buildCompanyResearch(companyHomeUrl, form, extractedInfo));
    setError("");
    recordUsage("会社URL調査", form.project_brief.length + form.client_company_info.length, "company-research", "success");
  }

  function toggleAutomation(key: keyof AutomationSettings) {
    setAutomationSettings((current) => ({ ...current, [key]: !current[key] }));
  }

  async function runDigitalCoworkerAgent() {
    if (isAgentRunning) return;
    setIsAgentRunning(true);
    setError("");
    setAgentSteps(initialAgentSteps);
    if (!companyResearch) {
      await runCompanyResearch();
    }

    for (let index = 0; index < initialAgentSteps.length; index += 1) {
      setAgentSteps((current) =>
        current.map((step, stepIndex) => ({
          ...step,
          status: stepIndex < index ? "done" : stepIndex === index ? "running" : "waiting"
        }))
      );
      await new Promise((resolve) => window.setTimeout(resolve, 450));
    }

    setAgentSteps((current) => current.map((step) => ({ ...step, status: "done" })));
    setMailResult(buildInternalMail("提案書送付と次回確認事項の共有", extractClientName(form), form.project_brief, "丁寧"));
    recordModeUsage("sales");
    recordUsage("AI Digital Coworker", allInputText(form).length + rawSourceText.length, "agent-workflow", "success");
    setRecentFeatures((current) => ["AI Digital Coworker", ...current.filter((item) => item !== "AI Digital Coworker")].slice(0, 5));
    setIsAgentRunning(false);
  }

  function updateField(field: keyof ProposalRequest, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function updateEasyField(field: keyof EasyInput, value: string) {
    setEasyInput((current) => ({ ...current, [field]: value }));
  }

  function updateMinimalField(field: keyof MinimalInput, value: string) {
    setMinimalInput((current) => ({ ...current, [field]: value }));
  }

  function toggleEasyPurpose(purpose: string) {
    setEasyInput((current) => ({
      ...current,
      purposes: current.purposes.includes(purpose)
        ? current.purposes.filter((item) => item !== purpose)
        : [...current.purposes, purpose]
    }));
  }

  function organizeEasyInput() {
    if (!canOrganizeEasyInput) {
      return;
    }
    setForm((current) => patchFormFromEasyInput(current, easyInput));
    setError("");
  }

  function organizeMinimalInput(openConfirm = false) {
    if (!minimalInput.companyName.trim() && !minimalInput.goal.trim() && !minimalInput.trouble.trim()) {
      setError("会社名、やりたいこと、困りごとのうち、分かる範囲で1つ以上入力してください。");
      return false;
    }
    const nextForm = patchFormFromMinimalInput(form, minimalInput);
    setForm(nextForm);
    setError("");
    if (openConfirm) {
      setIsConfirmOpen(true);
    }
    return true;
  }

  function applySourceExtraction(openConfirm = false) {
    if (!rawSourceText.trim() && !companyHomeUrl.trim()) {
      setError("案件メール、議事録、チャット、Ready Crew案件情報、または会社ホームページURLを入力してください。");
      return false;
    }

    const baseExtracted = extractProposalInfo(rawSourceText, companyHomeUrl);
    const nextExtracted = fillMissingExtractedInfo(baseExtracted, companyHomeUrl);
    const nextInsight = buildUrlInsight(companyHomeUrl, rawSourceText, nextExtracted);
    const nextAnswers = buildChatAnswersFromExtracted(baseExtracted);
    const nextMissingIndex = findNextMissingQuestionIndex(nextAnswers);
    const missingQuestion =
      nextMissingIndex >= 0
        ? `${chatQuestionFlow[nextMissingIndex].label}だけ教えてください。\n${chatQuestionFlow[nextMissingIndex].question}`
        : "必要な情報が揃いました。提案書を生成できます。";

    setExtractedInfo(nextExtracted);
    setUrlInsight(nextInsight);
    setChatAnswers(nextAnswers);
    setChatQuestionIndex(nextMissingIndex >= 0 ? nextMissingIndex : chatQuestionFlow.length);
    setAssistantQuestionCount(nextMissingIndex >= 0 ? 1 : 0);
    setChatDraft("");
    setForm((current) => fillMissingProposalForm(buildFormFromExtracted(current, nextExtracted, nextInsight)));
    setChatMessages([
      ...initialChatMessages,
      {
        id: `assistant-extract-${Date.now()}`,
        role: "assistant",
        text: `貼り付け情報を整理しました。
会社名：${nextExtracted.companyName || "未抽出"}
案件内容：${nextExtracted.projectContent || "未抽出"}
困りごと：${nextExtracted.trouble || "未抽出"}
予算：${nextExtracted.budget || "未抽出"}
納期：${nextExtracted.deadline || "未抽出"}
競合：${nextExtracted.competitor || "未抽出"}`
      },
      {
        id: `assistant-missing-${Date.now()}`,
        role: "assistant",
        text: nextMissingIndex >= 0 ? missingQuestion : "このまま「今の内容で生成する」から提案書を作成できます。"
      }
    ]);
    setError("");
    if (openConfirm) {
      setIsConfirmOpen(true);
    }
    return true;
  }

  function organizeSourceText() {
    applySourceExtraction(false);
  }

  function oneClickAutoGenerate() {
    if (rawSourceText.trim() || companyHomeUrl.trim()) {
      applySourceExtraction(true);
      return;
    }

    const nextForm = fillMissingProposalForm(Object.keys(chatAnswers).length > 0 ? applyChatAnswersToForm(form, chatAnswers) : form);
    if (nextForm.project_brief.trim().length < 20) {
      setError("ここに案件メールを貼るだけで始められます。URLだけでもOKです。分からない項目は空欄でOKです。");
      return;
    }

    setForm(nextForm);
    setError("");
    setIsConfirmOpen(true);
  }

  function autoPrepareProposal() {
    if (rawSourceText.trim() || companyHomeUrl.trim()) {
      applySourceExtraction(true);
      return;
    }

    if (minimalInput.companyName.trim() || minimalInput.goal.trim() || minimalInput.trouble.trim()) {
      organizeMinimalInput(true);
      return;
    }

    if (easyInput.projectType.trim() || easyInput.trouble.trim() || easyInput.purposes.length > 0) {
      const nextForm = fillMissingProposalForm(patchFormFromEasyInput(form, easyInput));
      setForm(nextForm);
      setError("");
      setIsConfirmOpen(true);
      return;
    }

    const nextForm = fillMissingProposalForm(Object.keys(chatAnswers).length > 0 ? applyChatAnswersToForm(form, chatAnswers) : form);
    if (nextForm.project_brief.trim().length < 20) {
      setError("案件メール、会社URL、最小入力、かんたん入力のいずれかを入れると、AIに全部おまかせできます。");
      return;
    }

    setForm(nextForm);
    setError("");
    setIsConfirmOpen(true);
  }

  function insertSourceTemplate(kind: SourceTemplateKind) {
    setRawSourceText(sourceTemplates[kind]);
    setError("");
  }

  async function handleDroppedFiles(files: FileList | null) {
    if (!files?.length) return;
    const fileArray = Array.from(files);
    setUploadedFiles(fileArray.map((file) => file.name));

    const readableParts = await Promise.all(
      fileArray.map(async (file) => {
        const canReadAsText =
          file.type.startsWith("text/") ||
          /\.(txt|md|csv|tsv|eml)$/i.test(file.name);
        if (!canReadAsText) {
          return `添付ファイル：${file.name}（${file.type || "形式不明"}）。内容はファイル名を解析メモとして反映。`;
        }
        try {
          return `添付ファイル：${file.name}\n${await file.text()}`;
        } catch {
          return `添付ファイル：${file.name}。内容の読み取りに失敗しました。`;
        }
      })
    );

    setRawSourceText((current) => [current, ...readableParts].filter(Boolean).join("\n\n"));
  }

  function handleDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    void handleDroppedFiles(event.dataTransfer.files);
  }

  function startVoiceInput() {
    const SpeechRecognition =
      (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionLike; webkitSpeechRecognition?: new () => SpeechRecognitionLike }).SpeechRecognition ||
      (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionLike; webkitSpeechRecognition?: new () => SpeechRecognitionLike }).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError("このブラウザでは音声入力に対応していません。Chromeなど対応ブラウザで試してください。");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "ja-JP";
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript ?? "")
        .join("");
      setRawSourceText((current) => [current, `音声入力：${transcript}`].filter(Boolean).join("\n"));
    };
    recognition.onerror = () => setError("音声入力に失敗しました。マイク許可を確認してください。");
    recognition.start();
  }

  function updatePreviewSlide(index: number, field: keyof PreviewSlide, value: string) {
    setEditablePreviewSlides((current) =>
      current.map((slide, slideIndex) => (slideIndex === index ? { ...slide, [field]: value } : slide))
    );
  }

  function createDailyReport() {
    setDailyReport(buildSalesDailyReport(form, meetingEvaluation));
    recordModeUsage("coach");
  }

  function createBossReport() {
    setBossReport(buildBossReport(form, dealEvaluation, missingItems));
    recordModeUsage("coach");
  }

  function generateMinutesMode() {
    const source = minutesInput.trim() || form.hearing_result || rawSourceText || form.project_brief;
    setMinutesResult(buildInternalMinutes(source));
    setError("");
    recordModeUsage("minutes");
    recordUsage("議事録AI", source.length, "minutes", "success");
  }

  function generateMailMode() {
    setMailResult(buildInternalMail(mailPurpose, mailRecipient, mailContent || form.project_brief, mailTone));
    setError("");
    recordModeUsage("mail");
    recordUsage("メール作成AI", (mailPurpose + mailRecipient + mailContent).length, "mail", "success");
  }

  function generateTaskMode() {
    const source = taskInput.trim() || form.hearing_result || rawSourceText || form.project_brief;
    setTaskResult(buildInternalTasks(source));
    setError("");
    recordModeUsage("tasks");
    recordUsage("タスク整理AI", source.length, "tasks", "success");
  }

  function generateFaqMode() {
    setFaqResult(buildInternalFaq(faqQuestion));
    setError("");
    recordModeUsage("faq");
    recordUsage("社内FAQ AI", faqQuestion.length, "faq", "success");
  }

  function generateSummaryMode() {
    const source = summaryInput.trim() || displayedMarkdown || rawSourceText || form.project_brief;
    setSummaryResult(buildInternalSummary(source));
    setError("");
    recordModeUsage("summary");
    recordUsage("資料要約AI", source.length, "summary", "success");
  }

  function generateReportMode() {
    const source = reportInput.trim() || liveMeetingMemo || form.hearing_result || form.project_brief;
    setReportResult(buildInternalReport(source));
    setError("");
    recordModeUsage("reports");
    recordUsage("日報/週報AI", source.length, "report", "success");
  }

  function startRoleplay() {
    const scenario = roleplayScenarios[roleplayScenario];
    setRoleplayMessages([{ role: "customer", text: `${scenario.customer}です。${scenario.firstMessage}` }]);
    setRoleplayFinished(false);
    setRoleplayDraft("");
  }

  function sendRoleplayMessage() {
    const message = roleplayDraft.trim();
    if (!message) return;
    const replies = [
      "ありがとうございます。費用感と進め方をもう少し具体的に知りたいです。",
      "社内説明に使える資料があると助かります。競合との差も見たいです。",
      "公開後に成果が出るかが不安です。運用面も提案に含められますか？"
    ];
    setRoleplayMessages((current) => [
      ...current,
      { role: "sales", text: message },
      { role: "customer", text: replies[Math.min(current.length, replies.length - 1)] }
    ]);
    setRoleplayDraft("");
    if (roleplayMessages.filter((item) => item.role === "sales").length >= 2) {
      setRoleplayFinished(true);
    }
  }

  function submitChatAnswer(event?: React.FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const answer = chatDraft.trim();
    if (!answer) {
      return;
    }

    if (chatQuestionIndex >= chatQuestionFlow.length) {
      setChatMessages((current) => [
        ...current,
        { id: `user-${Date.now()}`, role: "user", text: answer },
        {
          id: `assistant-${Date.now()}-extra`,
          role: "assistant",
          text: "追加情報として反映しました。必要であれば、この内容で提案書を生成できます。"
        }
      ]);
      setForm((current) => ({
        ...current,
        hearing_result: [current.hearing_result, answer].filter(Boolean).join("\n")
      }));
      setChatDraft("");
      setError("");
      return;
    }

    const question = chatQuestionFlow[chatQuestionIndex];
    const nextAnswers = { ...chatAnswers, [question.key]: answer };
    const nextIndex = findNextMissingQuestionIndex(nextAnswers);
    const nextReadiness = buildChatReadiness(nextAnswers);
    const canAskMore = nextIndex >= 0 && assistantQuestionCount < MAX_ASSISTANT_QUESTIONS;
    const nextAssistantText =
      canAskMore
        ? `${nextReadiness.ready ? "提案書を生成できます。精度を上げるため、未確認の項目だけ確認します。\n" : ""}${chatQuestionFlow[nextIndex].label}だけ教えてください。\n${chatQuestionFlow[nextIndex].question}`
        : "必要な情報が揃いました。提案書を生成できます。まだ未確認の項目があっても「今の内容で生成する」から進められます。";

    setChatMessages((current) => [
      ...current,
      { id: `user-${Date.now()}`, role: "user", text: answer },
      { id: `assistant-${Date.now()}-next`, role: "assistant", text: nextAssistantText }
    ]);
    setChatAnswers(nextAnswers);
    setChatQuestionIndex(canAskMore ? nextIndex : chatQuestionFlow.length);
    setAssistantQuestionCount((current) => (canAskMore ? Math.min(MAX_ASSISTANT_QUESTIONS, current + 1) : current));
    setChatDraft("");
    setForm((current) => applyChatAnswersToForm(current, nextAnswers));
    setError("");
  }

  function generateFromChatNow() {
    const nextForm = fillMissingProposalForm(Object.keys(chatAnswers).length > 0 ? applyChatAnswersToForm(form, chatAnswers) : form);
    if (nextForm.project_brief.trim().length < 20) {
      setError("まずはチャットで案件内容を1つ入力してください。途中でも生成できます。");
      return;
    }
    setForm(nextForm);
    setError("");
    setIsConfirmOpen(true);
  }

  function resetChat() {
    setChatMessages(initialChatMessages);
    setChatAnswers({});
    setChatQuestionIndex(0);
    setAssistantQuestionCount(0);
    setChatDraft("");
    setRawSourceText("");
    setCompanyHomeUrl("");
    setExtractedInfo(null);
    setUrlInsight(null);
    setForm(initialForm);
    setResult(null);
    setError("");
  }

  function persistHistory(nextHistory: HistoryEntry[]) {
    setHistory(nextHistory);
    try {
      window.localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory));
    } catch {
      setError("生成は完了しましたが、履歴のローカル保存に失敗しました。ブラウザの保存容量を確認してください。");
    }
  }

  function saveHistory(response: AnalysisResponse) {
    const entry: HistoryEntry = {
      id: `${Date.now()}`,
      createdAt: new Date().toISOString(),
      title: response.powerpoint_generation_data.deck_title || "提案書初稿",
      clientName: extractClientName(form, response),
      form,
      result: response
    };
    const nextHistory = [entry, ...history.filter((item) => item.id !== entry.id)].slice(0, MAX_HISTORY_COUNT);
    persistHistory(nextHistory);
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canGenerate) {
      setError("閲覧のみ権限では提案書を生成できません。adminまたはmemberでログインしてください。");
      return;
    }
    if (!canSubmit) {
      return;
    }
    setForm((current) => fillMissingProposalForm(current));
    setError("");
    setIsConfirmOpen(true);
  }

  async function generateProposal() {
    if (!canGenerate) {
      setError("閲覧のみ権限では提案書を生成できません。adminまたはmemberでログインしてください。");
      return;
    }
    setIsConfirmOpen(false);
    setIsLoading(true);
    setError("");
    setCopyState("idle");

    try {
      const response = await analyzeProposal(form);
      setResult(response);
      saveHistory(response);
      recordModeUsage("sales");
      recordUsage("提案書生成", allInputText(form).length, "markdown", "success");
      void refreshAccountData();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      recordUsage("提案書生成", allInputText(form).length, "markdown", "failure", friendly.category);
      setError(`${friendly.title}。${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function copyMarkdown() {
    if (!result?.markdown) {
      return;
    }

    await navigator.clipboard.writeText(buildExportMarkdown(result.markdown, form));
    setCopyState("copied");
    window.setTimeout(() => setCopyState("idle"), 1800);
  }

  function downloadMarkdown(targetResult = result, targetForm = form) {
    if (!targetResult?.markdown) {
      return;
    }

    const clientName = extractClientName(targetForm, targetResult);
    downloadTextFile(buildExportMarkdown(targetResult.markdown, targetForm), `${sanitizeFileName(clientName)}_提案書初稿.md`);
  }

  async function downloadPowerPointFor(targetResult: AnalysisResponse, targetForm: ProposalRequest, summary: boolean) {
    if (!canGenerate) {
      setError("閲覧のみ権限ではPowerPointを生成できません。adminまたはmemberでログインしてください。");
      return;
    }
    if (summary) {
      setIsDownloadingSummaryPowerPoint(true);
    } else {
      setIsDownloadingPowerPoint(true);
    }
    setError("");

    try {
      const downloader = summary ? downloadSummaryProposalPowerPoint : downloadProposalPowerPoint;
      await downloader(
        targetResult.powerpoint_generation_data,
        targetResult.analysis.win_probability,
        targetForm.project_brief,
        targetForm.client_company_info,
        targetForm.competitor_site_url,
        targetForm.competitor_company_name,
        targetForm.estimated_page_count,
        targetForm.cms_required,
        targetForm.contact_form_required,
        targetForm.special_function_required,
        targetForm.seo_required,
        targetForm.content_creation_required,
        targetForm.desired_launch_timing,
        targetForm.budget_range,
        targetForm.own_service_info,
        targetForm.past_proposal_template,
        targetForm.case_studies
      );
      recordUsage(summary ? "要約PowerPoint" : "PowerPoint", allInputText(targetForm).length, summary ? "summary-pptx" : "pptx", "success");
      setLastDownloadRetry(null);
      void refreshAccountData();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      recordUsage(summary ? "要約PowerPoint" : "PowerPoint", allInputText(targetForm).length, summary ? "summary-pptx" : "pptx", "failure", friendly.category);
      setLastDownloadRetry(summary ? "summary-pptx" : "pptx");
      setError(`${friendly.title}。${friendly.action}`);
    } finally {
      if (summary) {
        setIsDownloadingSummaryPowerPoint(false);
      } else {
        setIsDownloadingPowerPoint(false);
      }
    }
  }

  async function downloadPowerPoint() {
    if (!result) return;
    await downloadPowerPointFor(result, form, false);
  }

  async function downloadSummaryPowerPoint() {
    if (!result) return;
    await downloadPowerPointFor(result, form, true);
  }

  async function downloadEstimatePdfFor(targetResult: AnalysisResponse, targetForm: ProposalRequest) {
    if (!canGenerate) {
      setError("閲覧のみ権限では見積書PDFを生成できません。adminまたはmemberでログインしてください。");
      return;
    }
    setIsDownloadingEstimatePdf(true);
    setError("");

    try {
      await downloadEstimatePdf(
        targetResult.powerpoint_generation_data,
        targetForm,
        targetResult.analysis.win_probability
      );
      recordUsage("見積書PDF", allInputText(targetForm).length, "estimate-pdf", "success");
      setLastDownloadRetry(null);
      void refreshAccountData();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      recordUsage("見積書PDF", allInputText(targetForm).length, "estimate-pdf", "failure", friendly.category);
      setLastDownloadRetry("estimate-pdf");
      setError(`${friendly.title}。${friendly.action}`);
    } finally {
      setIsDownloadingEstimatePdf(false);
    }
  }

  async function downloadEstimatePdfCurrent() {
    if (!result) return;
    await downloadEstimatePdfFor(result, form);
  }

  async function retryLastDownload() {
    if (!result || !lastDownloadRetry) return;
    if (lastDownloadRetry === "pptx") {
      await downloadPowerPointFor(result, form, false);
      return;
    }
    if (lastDownloadRetry === "summary-pptx") {
      await downloadPowerPointFor(result, form, true);
      return;
    }
    await downloadEstimatePdfFor(result, form);
  }

  function restoreHistory(entry: HistoryEntry) {
    setForm(normalizeForm(entry.form));
    setInputMode("detail");
    setChatMessages([
      ...initialChatMessages,
      {
        id: `assistant-history-${Date.now()}`,
        role: "assistant",
        text: "生成履歴を読み込みました。右側の整理済み概要を確認し、必要に応じて提案書を再ダウンロードできます。"
      }
    ]);
    setChatAnswers({});
    setChatQuestionIndex(0);
    setAssistantQuestionCount(0);
    setChatDraft("");
    setResult(entry.result);
    setError("");
    setCopyState("idle");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function clearHistory() {
    persistHistory([]);
  }

  function loadChatSample(kind: SampleKind) {
    const sample = easySamples[kind];
    const company =
      kind === "renewal"
        ? "株式会社東都リビング。首都圏で賃貸・売買仲介、物件管理を展開する不動産会社です。"
        : kind === "recruit"
          ? "株式会社サンプル製作所。BtoB向け製造・保守サービスを展開する会社です。"
          : kind === "lp"
            ? "株式会社サンプルマーケティング。新規Webサービスの広告配信とリード獲得を強化している会社です。"
            : "株式会社サンプルSEO。BtoBサービスの検索流入と問い合わせ獲得を強化したい会社です。";
    const nextAnswers: ChatAnswers = {
      project: sample.projectType,
      company,
      trouble: sample.trouble,
      budget: sample.budget,
      deadline: sample.deadline,
      competitor: sample.competitorSiteUrl
    };

    fillSample(kind);
    setChatAnswers(nextAnswers);
    setChatQuestionIndex(chatQuestionFlow.length);
    setAssistantQuestionCount(0);
    setChatDraft("");
    setChatMessages([
      ...initialChatMessages,
      {
        id: `assistant-sample-${Date.now()}`,
        role: "assistant",
        text: "サンプル案件を読み込みました。右側の整理済み概要を確認し、そのまま提案書を生成できます。"
      }
    ]);
  }

  function fillSample(kind: SampleKind = "renewal") {
    const sample = easySamples[kind];
    const sampleClientInfo =
      kind === "renewal"
        ? "株式会社東都リビング\n首都圏で賃貸・売買仲介、物件管理を展開\n既存サイトURL：https://sample-realty.example.jp\n決裁者：代表取締役、窓口：営業企画部"
        : kind === "recruit"
          ? "株式会社サンプル製作所\n首都圏でBtoB向け製造・保守サービスを展開\n既存サイトURL：https://sample-company.example.jp\n決裁者：代表取締役、窓口：人事責任者"
          : kind === "lp"
            ? "株式会社サンプルマーケティング\n新規Webサービスの広告配信とリード獲得を強化中\n既存サイトURL：https://sample-service.example.jp\n決裁者：事業責任者、窓口：マーケティング責任者"
            : "株式会社サンプルSEO\nBtoBサービスの検索流入と問い合わせ獲得を強化中\n既存サイトURL：https://sample-seo.example.jp\n決裁者：営業責任者、窓口：マーケティング責任者";
    setEasyInput(sample);
    setForm((current) => ({
      ...patchFormFromEasyInput(current, sample),
      project_brief:
        kind === "renewal"
          ? sampleBrief
          : kind === "seo"
            ? `${buildProjectBriefFromEasyInput(sample)}
SEO改善の重点：検索流入が伸び悩んでおり、サービスページ、FAQ、導入事例、比較検討キーワードのコンテンツ設計を見直したい。
初回提案では、SEO課題、サイト構造、コンテンツ優先順位、KPI、概算費用を知りたい。`
            : buildProjectBriefFromEasyInput(sample),
      client_company_info: sampleClientInfo,
      competitor_company_name:
        kind === "renewal"
          ? "エリア大手不動産グループ"
          : kind === "recruit"
            ? "採用競合企業"
            : kind === "lp"
              ? "競合LPサービス"
              : "検索上位の同業サービス",
      estimated_page_count: kind === "renewal" ? "18ページ" : kind === "recruit" ? "10ページ" : kind === "lp" ? "1ページ" : "12ページ",
      special_function_required: kind === "renewal" ? "物件検索あり" : "",
      content_creation_required: kind === "lp" ? "原稿作成あり" : "原稿作成一部あり",
      hearing_result:
        kind === "renewal"
          ? "問い合わせ数の増加を最優先にしたい。CMSはWordPressで進める方針。予算は350万〜500万円。公開希望は2026年10月末。物件登録データの連携方法は未確認。年間問い合わせ目標は現状比150%。"
          : kind === "recruit"
            ? "応募数と応募者の質を改善したい。社員インタビューと職種紹介を入れたい。公開時期は3か月以上で検討。採用責任者と代表が確認する。"
            : kind === "lp"
              ? "広告配信用LPとして早めに公開したい。問い合わせフォームとCTAを重視。予算は100〜300万円。訴求整理と原稿作成も相談したい。"
              : "自然検索流入と問い合わせ数を改善したい。既存記事はあるが成果につながっていない。優先キーワード、FAQ、導入事例、サービスページ改善を提案してほしい。予算は100〜300万円。",
      own_service_info: "Webサイト制作、情報設計、CMS構築、SEO初期設計、公開後の改善運用、月次レポートを支援",
      past_proposal_template: "表紙、提案サマリー、現状理解、競合比較、ターゲット分析、Web戦略、サイトマップ、KPI、制作方針、スケジュール、体制、費用概算、今後の進め方",
      case_studies:
        kind === "recruit"
          ? "採用サイトA：応募数160%増加\n製造業B：説明会予約数1.7倍"
          : kind === "lp"
            ? "SaaS企業A：資料請求CV率1.9倍\n新サービスLP：広告CPA25%改善"
            : kind === "seo"
              ? "BtoBサービスA：自然検索流入2.4倍\n専門サービスB：問い合わせ件数170%増加"
              : "不動産会社A：問い合わせ件数150%増加\n不動産会社B：CV率1.8倍\n住宅販売会社C：自然検索流入2.1倍"
    }));
    setError("");
  }

  return (
    <AuthGate>
    <main className={`app-shell ${isDarkMode ? "dark-mode" : ""}`}>
      <Header isDarkMode={isDarkMode} onToggleDarkMode={() => setIsDarkMode((current) => !current)} />
      <Dashboard
        dashboardMetrics={dashboardMetrics}
        monthlyDashboardMetrics={monthlyDashboardMetrics}
        operationDashboardMetrics={operationDashboardMetrics}
      />

      <section className="work-mode-panel" aria-label="業務モード切り替え">
        <div className="section-heading">
          <p className="eyebrow">Version 4.0</p>
          <h2>AI社員が営業業務を一緒に進めるワークスペース</h2>
          <p>営業提案から議事録、メール、タスク整理、日報まで、1つの画面で切り替えて使えます。</p>
        </div>
        <div className="work-mode-tabs" role="tablist" aria-label="業務モード">
          {workModeTabs.map((mode) => (
            <button
              aria-selected={activeMode === mode.key}
              className={activeMode === mode.key ? "is-active" : ""}
              key={mode.key}
              onClick={() => setActiveMode(mode.key)}
              role="tab"
              type="button"
            >
              <strong>{mode.label}</strong>
              <span>{mode.note}</span>
            </button>
          ))}
        </div>
        <div className="recent-feature-row">
          <strong>最近使った機能</strong>
          <span>{recentFeatures.length ? recentFeatures.join(" / ") : "まだ生成履歴はありません"}</span>
        </div>
      </section>

      <SecurityNotice />
      <HealthStatus onChange={setHealthSnapshot} />
      <SettingsPanel
        health={healthSnapshot}
        isAuthenticated
        usageLogs={usageLogs}
        currentUser={currentUser}
        dbLogCount={dbLogCount}
      />
      <PermissionNotice role={currentUser?.role} />
      {currentUser?.role === "admin" && (
        <>
          <AdminUsersPanel users={managedUsers} onCreateUser={handleCreateUser} onToggleUser={handleToggleUser} />
          <AdminAuditLogPanel logs={auditLogs} />
        </>
      )}
      <CrmPanel customers={crmCustomers} projects={crmProjects} />

      <section className="digital-coworker-panel" aria-label="AI Digital Coworker">
        <div className="digital-coworker-hero">
          <div>
            <p className="eyebrow">AI Digital Coworker</p>
            <h2>案件を受けたら、AI社員が順番に進めます</h2>
            <p>会社調査、競合調査、提案書作成、見積、メール準備までを、進行状況つきで整理します。</p>
          </div>
          <button className="primary-button" type="button" onClick={runDigitalCoworkerAgent} disabled={isAgentRunning}>
            {isAgentRunning ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Sparkles size={18} aria-hidden="true" />}
            {isAgentRunning ? "AI社員が実行中" : "AI社員に一括実行"}
          </button>
        </div>

        <div className="digital-grid">
          <article className="digital-card browser-use-card">
            <div className="card-title-row">
              <div>
                <span>Browser Use連携</span>
                <strong>会社URLから調査観点を作成</strong>
              </div>
              <button className="secondary-button" type="button" onClick={runCompanyResearch}>
                会社調査を実行
              </button>
            </div>
            <label className="field">
              <span>会社URL</span>
              <input
                value={companyHomeUrl}
                onChange={(event) => setCompanyHomeUrl(event.target.value)}
                placeholder="https://example.co.jp"
              />
            </label>
            {companyResearch ? (
              <div className="research-result-grid">
                <div><span>会社概要</span><p>{companyResearch.overview}</p></div>
                <div><span>競合</span><ul>{companyResearch.competitors.map((item) => <li key={item}>{item}</li>)}</ul></div>
                <div><span>採用</span><p>{companyResearch.recruitment}</p></div>
                <div><span>ニュース</span><ul>{companyResearch.news.map((item) => <li key={item}>{item}</li>)}</ul></div>
                <div><span>サービス</span><ul>{companyResearch.services.map((item) => <li key={item}>{item}</li>)}</ul></div>
                <div><span>SNS</span><ul>{companyResearch.sns.map((item) => <li key={item}>{item}</li>)}</ul></div>
              </div>
            ) : (
              <p className="helper-text">現時点では自動送信やログイン操作は行いません。公開情報を確認する観点をAIが整理します。</p>
            )}
          </article>

          <article className="digital-card">
            <div className="card-title-row">
              <div>
                <span>AIエージェント進行状況</span>
                <strong>順番に業務を実行</strong>
              </div>
            </div>
            <div className="agent-step-list">
              {agentSteps.map((step, index) => (
                <div className={`agent-step is-${step.status}`} key={step.label}>
                  <span>{index + 1}</span>
                  <div>
                    <strong>{step.label}</strong>
                    <p>{step.detail}</p>
                  </div>
                  <small>{step.status === "done" ? "完了" : step.status === "running" ? "実行中" : "待機"}</small>
                </div>
              ))}
            </div>
          </article>
        </div>

        <div className="digital-grid digital-grid-wide">
          <article className="digital-card ai-employee-card">
            <div className="card-title-row">
              <div>
                <span>AI社員</span>
                <strong>役割を選ぶと提案の見方が変わります</strong>
              </div>
            </div>
            <div className="ai-employee-grid">
              {aiEmployeeRoles.map((role) => (
                <button
                  className={selectedAiEmployee === role.key ? "is-active" : ""}
                  key={role.key}
                  onClick={() => setSelectedAiEmployee(role.key)}
                  type="button"
                >
                  <strong>{role.label}</strong>
                  <span>{role.mission}</span>
                </button>
              ))}
            </div>
            <div className="role-guidance-box">
              <strong>{aiEmployeeGuidance.title}</strong>
              <ul>{aiEmployeeGuidance.items.map((item) => <li key={item}>{item}</li>)}</ul>
            </div>
          </article>

          <article className="digital-card automation-card">
            <div className="card-title-row">
              <div>
                <span>Automations</span>
                <strong>定期確認の設定UI</strong>
              </div>
            </div>
            <div className="automation-list">
              {[
                { key: "morning" as const, label: "毎朝確認", note: "Ready Crew案件と優先度を毎朝整理" },
                { key: "weekly" as const, label: "毎週確認", note: "提案中案件、未対応タスク、失注リスクを確認" },
                { key: "deadline" as const, label: "締切前通知", note: "公開希望日・提案期限前に確認事項を通知" }
              ].map((item) => (
                <button className={automationSettings[item.key] ? "is-active" : ""} key={item.key} onClick={() => toggleAutomation(item.key)} type="button">
                  <span>{automationSettings[item.key] ? "ON" : "OFF"}</span>
                  <div>
                    <strong>{item.label}</strong>
                    <p>{item.note}</p>
                  </div>
                </button>
              ))}
            </div>
          </article>
        </div>

        <div className="digital-grid digital-grid-wide">
          <article className="digital-card mcp-settings-card">
            <div className="card-title-row">
              <div>
                <span>MCP対応UI</span>
                <strong>将来接続する社内・営業ツール</strong>
              </div>
            </div>
            <div className="mcp-card-grid">
              {mcpConnectorCards.map((connector, index) => (
                <article key={connector}>
                  <strong>{connector}</strong>
                  <span>{index < 3 ? "未接続" : "接続予定"}</span>
                </article>
              ))}
            </div>
          </article>

          <article className="digital-card review-chain-card">
            <div className="card-title-row">
              <div>
                <span>AIレビュー</span>
                <strong>AI社員同士で生成物を改善</strong>
              </div>
            </div>
            <div className="review-chain">
              {aiCoworkerReviews.map((review, index) => (
                <div key={review.reviewer}>
                  <span>{index + 1}</span>
                  <div>
                    <strong>{review.reviewer}</strong>
                    <p>{review.comment}</p>
                    <small>{review.improvement}</small>
                  </div>
                </div>
              ))}
            </div>
          </article>
        </div>
      </section>

      {activeMode === "sales" && (
        <>
      <section className="capability-panel" aria-label="このAIでできること">
        <div className="section-heading">
          <p className="eyebrow">Value</p>
          <h2>このAIでできること</h2>
        </div>
        <div className="capability-grid">
          <article>
            <strong>提案書作成時間を短縮</strong>
            <p>案件概要から提案サマリー、課題、方針、構成案まで一気に初稿化します。</p>
          </article>
          <article>
            <strong>不足情報をAIがチェック</strong>
            <p>予算、納期、決裁者、競合、CMS、SEOなど、次回確認すべき情報を整理します。</p>
          </article>
          <article>
            <strong>PowerPoint・PDFを自動生成</strong>
            <p>詳細PPTX、要約PPTX、見積書PDFをダウンロードして、営業資料作成に使えます。</p>
          </article>
        </div>
      </section>

      <section className="before-after-panel" aria-label="Before After比較">
        <div>
          <span>Before</span>
          <strong>手作業で2〜3時間</strong>
          <p>案件整理、構成検討、資料たたき台、見積整理を個別に作成。</p>
        </div>
        <div>
          <span>After</span>
          <strong>AIで20〜30分に短縮</strong>
          <p>初稿生成後、人が30分程度で確認・調整して提出準備へ。</p>
        </div>
      </section>

      <section className="usage-steps" aria-label="使い方4ステップ">
        <article>
          <span>1</span>
          <div>
            <strong>情報を貼り付ける</strong>
            <p>案件メール、議事録、チャット、Ready Crew案件情報をそのまま貼り付けます。</p>
          </div>
        </article>
        <article>
          <span>2</span>
          <div>
            <strong>AIが整理する</strong>
            <p>会社名、案件内容、目的、予算、納期、競合、CMSを自動抽出します。</p>
          </div>
        </article>
        <article>
          <span>3</span>
          <div>
            <strong>不足情報だけ回答</strong>
            <p>抽出できなかった項目だけ、AI営業アシスタントが追加で質問します。</p>
          </div>
        </article>
        <article>
          <span>4</span>
          <div>
            <strong>提案書生成</strong>
            <p>Markdown、PPTX、要約PPTX、見積書PDFを保存できます。</p>
          </div>
        </article>
      </section>

      <section className="extractor-panel" aria-label="AI情報抽出モード">
        <div className="extractor-heading">
          <div>
            <p className="eyebrow">AI Extract Mode</p>
            <h2>案件メール・議事録・チャット・Ready Crew案件情報を<br />そのまま貼り付けてください</h2>
          </div>
          <div className="extractor-score">
            <span>案件化しやすさ</span>
            <strong>{salesOpportunityScore.stars}</strong>
            <small>{salesOpportunityScore.label}</small>
          </div>
        </div>

        <div className="auto-generate-bar">
          <div>
            <strong>まずはAIにおまかせ生成</strong>
            <p>貼り付け情報やURLから自動整理し、生成前確認まで進めます。</p>
          </div>
          <button className="primary-button auto-generate-button" type="button" onClick={oneClickAutoGenerate}>
            <Sparkles size={18} aria-hidden="true" />
            まずはAIにおまかせ生成
          </button>
          <button className="secondary-button auto-generate-button" type="button" onClick={autoPrepareProposal}>
            <Bot size={18} aria-hidden="true" />
            AIに全部おまかせ
          </button>
        </div>

        <div className="simple-guide-row" aria-label="入力ガイド">
          <span>ここに案件メールを貼るだけ</span>
          <span>URLだけでもOK</span>
          <span>分からない項目は空欄でOK</span>
        </div>

        <div
          className="drop-voice-panel"
          onDragOver={(event) => event.preventDefault()}
          onDrop={handleDrop}
          aria-label="ファイルドラッグアンドドロップ"
        >
          <div>
            <UploadCloud size={20} aria-hidden="true" />
            <strong>PDF / Word / PowerPoint / Excel / メール(.eml)をドラッグ</strong>
            <p>{uploadedFiles.length ? `読み込み: ${uploadedFiles.join("、")}` : "ファイル名と読めるテキストを案件情報に追加します。"}</p>
          </div>
          <div className="drop-actions">
            <label className="secondary-button file-pick-button">
              ファイルを選択
              <input
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.eml,.txt,.md,.csv"
                onChange={(event) => void handleDroppedFiles(event.target.files)}
              />
            </label>
            <button className="secondary-button" type="button" onClick={startVoiceInput}>
              <Mic size={16} aria-hidden="true" />
              音声入力
            </button>
          </div>
        </div>

        <div className="extractor-flow" aria-label="4ステップ">
          <div><span>1</span><strong>情報を貼り付ける</strong></div>
          <div><span>2</span><strong>AIが整理する</strong></div>
          <div><span>3</span><strong>不足情報だけ回答</strong></div>
          <div><span>4</span><strong>提案書生成</strong></div>
        </div>

        <div className="extractor-grid">
          <label className="field extractor-main-input">
            <div className="field-title-row">
              <span>貼り付け情報</span>
              <small>Ready Crew案件メール、Zoom議事録、Slack、Teams、Chatwork、メールをそのまま貼り付け</small>
            </div>
            <div className="template-button-row" aria-label="コピー用テンプレート">
              <button className="secondary-button" type="button" onClick={() => insertSourceTemplate("readyCrew")}>
                Ready Crew案件メールを貼る例
              </button>
              <button className="secondary-button" type="button" onClick={() => insertSourceTemplate("hearing")}>
                ヒアリングメモを貼る例
              </button>
              <button className="secondary-button" type="button" onClick={() => insertSourceTemplate("slack")}>
                Slack相談文を貼る例
              </button>
            </div>
            <textarea
              value={rawSourceText}
              onChange={(event) => setRawSourceText(event.target.value)}
              placeholder="例：
Ready Crew案件情報
株式会社サンプル不動産様。Webサイトリニューアル希望。
現行サイトが古く、問い合わせ数を増やしたい。
予算は300万〜500万円。10月末公開希望。
CMSはWordPress希望。競合：https://example.co.jp"
              rows={9}
            />
          </label>

          <div className="url-analysis-box">
            <label className="field">
              <div className="field-title-row">
                <span>会社ホームページURL</span>
                <small>URLだけでも解析メモを作成</small>
              </div>
              <input
                value={companyHomeUrl}
                onChange={(event) => setCompanyHomeUrl(event.target.value)}
                placeholder="https://example.co.jp"
              />
            </label>
            <button className="primary-button" type="button" onClick={organizeSourceText}>
              <Sparkles size={18} aria-hidden="true" />
              AIが整理する
            </button>
            <div className="score-reason-box">
              <strong>スコア理由</strong>
              <ul>
                {salesOpportunityScore.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {(extractedInfo || urlInsight) && (
          <div className="extractor-result-grid">
            {extractedInfo && (
              <article className="extractor-result-card">
                <strong>AI抽出結果</strong>
                <dl>
                  <div><dt>会社名</dt><dd>{extractedInfo.companyName || "未抽出"}</dd></div>
                  <div><dt>担当者</dt><dd>{extractedInfo.contactPerson || "未抽出"}</dd></div>
                  <div><dt>案件内容</dt><dd>{extractedInfo.projectContent || "未抽出"}</dd></div>
                  <div><dt>目的</dt><dd>{extractedInfo.purposes.join("、") || "未抽出"}</dd></div>
                  <div><dt>困りごと</dt><dd>{extractedInfo.trouble || "未抽出"}</dd></div>
                  <div><dt>予算</dt><dd>{extractedInfo.budget || "未抽出"}</dd></div>
                  <div><dt>納期</dt><dd>{extractedInfo.deadline || "未抽出"}</dd></div>
                  <div><dt>競合</dt><dd>{extractedInfo.competitor || "未抽出"}</dd></div>
                  <div><dt>CMS</dt><dd>{extractedInfo.cms || "未抽出"}</dd></div>
                  <div><dt>ターゲット</dt><dd>{extractedInfo.target || "未抽出"}</dd></div>
                  <div><dt>SEO課題</dt><dd>{extractedInfo.seoIssue || "未抽出"}</dd></div>
                  <div><dt>問い合わせ内容</dt><dd>{extractedInfo.inquiryDetails || "未抽出"}</dd></div>
                </dl>
              </article>
            )}

            {urlInsight && (
              <article className="extractor-result-card">
                <strong>URL解析メモ</strong>
                <dl>
                  <div><dt>会社概要</dt><dd>{urlInsight.companyOverview}</dd></div>
                  <div><dt>事業内容</dt><dd>{urlInsight.business}</dd></div>
                  <div><dt>強み</dt><dd>{urlInsight.strengths}</dd></div>
                  <div><dt>弱み</dt><dd>{urlInsight.weaknesses}</dd></div>
                  <div><dt>競合</dt><dd>{urlInsight.competitors}</dd></div>
                  <div><dt>サービス</dt><dd>{urlInsight.services}</dd></div>
                  <div><dt>採用情報</dt><dd>{urlInsight.recruitment}</dd></div>
                  <div><dt>SEO状況</dt><dd>{urlInsight.seoStatus}</dd></div>
                </dl>
              </article>
            )}
          </div>
        )}
      </section>

        </>
      )}

      {activeMode === "coach" && (
      <section className="meeting-coach-panel" aria-label="AI商談コーチ">
        <div className="coach-heading">
          <div>
            <p className="eyebrow">AI Meeting Coach</p>
            <h2>商談前・商談中・商談後をAIがサポート</h2>
          </div>
          <div className="coach-score">
            <span>AI受注予測</span>
            <strong>{dealEvaluation.riskLabel}</strong>
            <small>受注確率 {dealEvaluation.probability}%</small>
          </div>
        </div>

        <div className="coach-grid">
          <article className="coach-card checklist-card">
            <strong>商談前チェックリスト</strong>
            <ul>
              {preMeetingChecklist.map((item) => (
                <li className={item.done ? "is-done" : ""} key={item.label}>
                  <span>{item.done ? "✓" : "□"}</span>
                  {item.label}
                </li>
              ))}
            </ul>
          </article>

          <article className="coach-card question-coach-card">
            <strong>この案件で聞いた方がいい質問 TOP10</strong>
            <div className="coach-question-list">
              {coachQuestions.map((item) => (
                <div key={item.question}>
                  <span>{starsFromPriority(item.priority)}</span>
                  <p>{item.question}</p>
                  <small>{item.reason}</small>
                </div>
              ))}
            </div>
          </article>

          <article className="coach-card realtime-card">
            <strong>商談リアルタイム支援</strong>
            <textarea
              value={liveMeetingMemo}
              onChange={(event) => setLiveMeetingMemo(event.target.value)}
              placeholder="商談中のメモを入力すると、次に聞くべき質問を表示します。"
              rows={7}
            />
            <div className="next-question-box">
              <span>おすすめ質問</span>
              <p>{realtimeQuestion}</p>
            </div>
          </article>
        </div>

        <div className="coach-after-grid">
          <article className="coach-card meeting-evaluation-card">
            <strong>AI商談評価</strong>
            <div className="meeting-score-row">
              <span>{meetingEvaluation.total}点</span>
              <p>{meetingEvaluation.comment}</p>
            </div>
            <div className="quality-grid">
              <div><span>ヒアリング力</span><strong>{meetingEvaluation.hearing}</strong></div>
              <div><span>提案力</span><strong>{meetingEvaluation.proposal}</strong></div>
              <div><span>クロージング</span><strong>{meetingEvaluation.closing}</strong></div>
              <div><span>質問内容</span><strong>{meetingEvaluation.questions}</strong></div>
              <div><span>情報収集</span><strong>{meetingEvaluation.information}</strong></div>
            </div>
          </article>

          <article className="coach-card feedback-card">
            <strong>AIフィードバック</strong>
            <div className="feedback-columns">
              <div>
                <span>良かった点</span>
                <ul>{meetingEvaluation.goodPoints.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
              <div>
                <span>改善点</span>
                <ul>{meetingEvaluation.improvements.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
              <div>
                <span>次回意識すること</span>
                <ul>{meetingEvaluation.nextFocus.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
            </div>
          </article>

          <article className="coach-card next-prep-card">
            <strong>AI次回商談準備</strong>
            <div className="feedback-columns">
              <div>
                <span>確認すべき内容</span>
                <ul>{(nextMeetingPrep.confirmations.length ? nextMeetingPrep.confirmations : ["不足情報は大きくありません"]).map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
              <div>
                <span>宿題</span>
                <ul>{nextMeetingPrep.homework.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
              <div>
                <span>提出物</span>
                <ul>{nextMeetingPrep.deliverables.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
            </div>
          </article>
        </div>

        <div className="coach-output-grid">
          <article className="coach-card win-advice-card">
            <strong>AI受注率向上アドバイス</strong>
            <div className="feedback-columns">
              <div>
                <span>提案書で追加</span>
                <ul>{winRateCoachAdvice.additions.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
              <div>
                <span>競合との差別化</span>
                <ul>{winRateCoachAdvice.differentiation.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
              <div>
                <span>お客様が喜ぶ提案</span>
                <ul>{winRateCoachAdvice.delight.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
            </div>
          </article>

          <article className="coach-card report-card">
            <strong>AI営業レポート</strong>
            <div className="report-actions">
              <button className="secondary-button" type="button" onClick={createDailyReport}>営業日報を作成</button>
              <button className="secondary-button" type="button" onClick={createBossReport}>上司へ報告</button>
            </div>
            {dailyReport && (
              <div className="draft-box">
                <strong>本日の活動</strong>
                <ul>{dailyReport.activities.map((item) => <li key={item}>{item}</li>)}</ul>
                <strong>商談内容</strong>
                <ul>{dailyReport.meeting.map((item) => <li key={item}>{item}</li>)}</ul>
                <strong>成果</strong>
                <ul>{dailyReport.results.map((item) => <li key={item}>{item}</li>)}</ul>
                <strong>課題</strong>
                <ul>{dailyReport.issues.map((item) => <li key={item}>{item}</li>)}</ul>
                <strong>明日の予定</strong>
                <ul>{dailyReport.tomorrow.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
            )}
            {bossReport && (
              <div className="draft-box">
                <strong>上司報告</strong>
                <p>{bossReport}</p>
              </div>
            )}
          </article>

          <article className="coach-card knowledge-card">
            <strong>営業ナレッジ蓄積</strong>
            <div className="knowledge-columns">
              <div><span>似た案件</span><p>{knowledgeGroups.similar.map((entry) => entry.clientName).join("、") || "履歴待ち"}</p></div>
              <div><span>成功案件</span><p>{knowledgeGroups.success.map((entry) => entry.clientName).join("、") || "履歴待ち"}</p></div>
              <div><span>失注案件</span><p>{knowledgeGroups.lost.map((entry) => entry.clientName).join("、") || "履歴待ち"}</p></div>
            </div>
          </article>

          <article className="coach-card roleplay-card">
            <strong>AIロールプレイ</strong>
            <div className="roleplay-controls">
              <select value={roleplayScenario} onChange={(event) => setRoleplayScenario(event.target.value as RoleplayScenario)}>
                {Object.entries(roleplayScenarios).map(([key, scenario]) => (
                  <option key={key} value={key}>{scenario.label}</option>
                ))}
              </select>
              <button className="secondary-button" type="button" onClick={startRoleplay}>模擬商談を開始</button>
            </div>
            <div className="roleplay-thread">
              {roleplayMessages.map((message, index) => (
                <div className={`roleplay-message ${message.role}`} key={`${message.role}-${index}`}>
                  <span>{message.role === "customer" ? "お客様役" : "営業担当"}</span>
                  <p>{message.text}</p>
                </div>
              ))}
            </div>
            <div className="roleplay-compose">
              <input value={roleplayDraft} onChange={(event) => setRoleplayDraft(event.target.value)} placeholder="お客様へ回答してください" />
              <button className="secondary-button" type="button" onClick={sendRoleplayMessage}>送信</button>
            </div>
            {roleplayFinished && (
              <div className="draft-box">
                <strong>評価</strong>
                <p>課題確認と次回提案への誘導は良好です。予算・決裁者・比較対象を早めに確認するとさらに良くなります。</p>
                <strong>改善点</strong>
                <p>お客様の不安を復唱し、成果指標と提出物を明確にしましょう。</p>
                <strong>おすすめ回答</strong>
                <p>「まず成果目標を確認し、必須範囲とオプション範囲に分けて、社内説明しやすい要約資料もご用意します。」</p>
              </div>
            )}
          </article>
        </div>
      </section>

      )}

      {activeMode === "minutes" && (
        <section className="business-mode-panel" aria-label="議事録AI">
          <div className="business-mode-heading">
            <div>
              <p className="eyebrow">Minutes AI</p>
              <h2>議事録AI</h2>
              <p>会議メモ、文字起こし、チャットログから、決定事項・未決事項・ToDoを整理します。</p>
            </div>
            <button className="primary-button" type="button" onClick={generateMinutesMode}>
              <FileText size={18} aria-hidden="true" />
              議事録を生成
            </button>
          </div>
          <div className="business-mode-grid">
            <label className="field business-input-card">
              <span>会議メモ・文字起こし・チャットログ</span>
              <textarea
                value={minutesInput}
                onChange={(event) => setMinutesInput(event.target.value)}
                placeholder="例：本日の商談では、10月公開、WordPress希望、問い合わせ導線改善が主題。予算は次回確認。担当は営業が資料を作成し、制作側が概算見積を確認。"
                rows={12}
              />
            </label>
            <article className="business-output-card">
              <strong>出力結果</strong>
              {minutesResult ? (
                <div className="business-output-sections">
                  <div><span>議事録</span><ul>{minutesResult.minutes.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  <div><span>決定事項</span><ul>{minutesResult.decisions.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  <div><span>未決事項</span><ul>{minutesResult.unresolved.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  <div>
                    <span>ToDo / 担当者 / 期限</span>
                    <div className="mini-table">
                      {minutesResult.todos.map((todo) => (
                        <div key={todo.task}><strong>{todo.task}</strong><small>{todo.owner} / {todo.deadline}</small></div>
                      ))}
                    </div>
                  </div>
                  <div><span>次回確認事項</span><ul>{minutesResult.nextConfirmations.map((item) => <li key={item}>{item}</li>)}</ul></div>
                </div>
              ) : (
                <p className="empty-state">会議メモを入力して「議事録を生成」を押してください。未入力の場合は営業提案AIの商談メモから作成します。</p>
              )}
            </article>
          </div>
        </section>
      )}

      {activeMode === "mail" && (
        <section className="business-mode-panel" aria-label="メール作成AI">
          <div className="business-mode-heading">
            <div>
              <p className="eyebrow">Mail AI</p>
              <h2>メール作成AI</h2>
              <p>目的、相手、伝えたい内容、トーンから、件名・本文・返信案を作成します。</p>
            </div>
            <button className="primary-button" type="button" onClick={generateMailMode}>
              <Mail size={18} aria-hidden="true" />
              メール文を作成
            </button>
          </div>
          <div className="business-mode-grid">
            <div className="business-input-card stacked-fields">
              <label className="field"><span>目的</span><input value={mailPurpose} onChange={(event) => setMailPurpose(event.target.value)} placeholder="例：提案書初稿の送付" /></label>
              <label className="field"><span>相手</span><input value={mailRecipient} onChange={(event) => setMailRecipient(event.target.value)} placeholder="例：株式会社サンプル ご担当者様" /></label>
              <label className="field"><span>トーン</span><select value={mailTone} onChange={(event) => setMailTone(event.target.value)}><option>丁寧</option><option>やわらかい</option><option>簡潔</option><option>社内向け</option></select></label>
              <label className="field"><span>伝えたい内容</span><textarea value={mailContent} onChange={(event) => setMailContent(event.target.value)} placeholder="共有したい要点を箇条書きで入力" rows={7} /></label>
            </div>
            <article className="business-output-card">
              <strong>出力結果</strong>
              {mailResult ? (
                <div className="business-output-sections">
                  <div><span>件名</span><p>{mailResult.subject}</p></div>
                  <div><span>本文</span><pre>{mailResult.body}</pre></div>
                  <div><span>返信案</span><p>{mailResult.reply}</p></div>
                  <div><span>丁寧版</span><p>{mailResult.polite}</p></div>
                  <div><span>短縮版</span><p>{mailResult.short}</p></div>
                </div>
              ) : (
                <p className="empty-state">目的と伝えたい内容を入力すると、顧客向けメールのたたき台を作成します。</p>
              )}
            </article>
          </div>
        </section>
      )}

      {activeMode === "tasks" && (
        <section className="business-mode-panel" aria-label="タスク整理AI">
          <div className="business-mode-heading">
            <div>
              <p className="eyebrow">Task AI</p>
              <h2>タスク整理AI</h2>
              <p>メモ、議事録、依頼文をタスク一覧・優先度・担当者・期限に分解します。</p>
            </div>
            <button className="primary-button" type="button" onClick={generateTaskMode}>
              <CheckCircle2 size={18} aria-hidden="true" />
              タスクに分解
            </button>
          </div>
          <div className="business-mode-grid">
            <label className="field business-input-card">
              <span>メモ・議事録・依頼文</span>
              <textarea value={taskInput} onChange={(event) => setTaskInput(event.target.value)} placeholder="依頼内容や会議メモをそのまま貼り付け" rows={12} />
            </label>
            <article className="business-output-card">
              <strong>出力結果</strong>
              {taskResult ? (
                <div className="business-output-sections">
                  <div className="mini-table">
                    {taskResult.tasks.map((task) => (
                      <div key={task.task}>
                        <strong>{task.task}</strong>
                        <small>優先度: {task.priority} / 担当者: {task.owner} / 期限: {task.deadline}</small>
                        <p>{task.risk}</p>
                      </div>
                    ))}
                  </div>
                  <div><span>次にやること</span><p>{taskResult.nextAction}</p></div>
                </div>
              ) : (
                <p className="empty-state">依頼文を貼ると、すぐ動けるタスク一覧に変換します。</p>
              )}
            </article>
          </div>
        </section>
      )}

      {activeMode === "faq" && (
        <section className="business-mode-panel" aria-label="社内FAQ AI">
          <div className="business-mode-heading">
            <div>
              <p className="eyebrow">FAQ AI</p>
              <h2>社内FAQ AI</h2>
              <p>社内ルールや資料の確認事項に対して、回答案・確認部署・参照資料を整理します。</p>
            </div>
            <button className="primary-button" type="button" onClick={generateFaqMode}>
              <Bot size={18} aria-hidden="true" />
              回答案を作成
            </button>
          </div>
          <div className="business-mode-grid">
            <label className="field business-input-card">
              <span>質問文</span>
              <textarea value={faqQuestion} onChange={(event) => setFaqQuestion(event.target.value)} placeholder="例：概算見積の社内確認フローを教えてください" rows={8} />
              <small>外部DB連携は未実装です。今後MCP/Google Drive連携で精度を高める想定です。</small>
            </label>
            <article className="business-output-card">
              <strong>出力結果</strong>
              {faqResult ? (
                <div className="business-output-sections">
                  <div><span>回答案</span><p>{faqResult.answer}</p></div>
                  <div><span>確認が必要な部署</span><p>{faqResult.department}</p></div>
                  <div><span>参照すべき資料</span><ul>{faqResult.references.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  <div><span>注意点</span><ul>{faqResult.notes.map((item) => <li key={item}>{item}</li>)}</ul></div>
                </div>
              ) : (
                <p className="empty-state">質問を入力すると、社内確認の入口になる回答案を作成します。</p>
              )}
            </article>
          </div>
        </section>
      )}

      {activeMode === "summary" && (
        <section className="business-mode-panel" aria-label="資料要約AI">
          <div className="business-mode-heading">
            <div>
              <p className="eyebrow">Summary AI</p>
              <h2>資料要約AI</h2>
              <p>長文、議事録、提案書、メモを3行要約・重要ポイント・アクションに整理します。</p>
            </div>
            <button className="primary-button" type="button" onClick={generateSummaryMode}>
              <FileCheck2 size={18} aria-hidden="true" />
              資料を要約
            </button>
          </div>
          <div className="business-mode-grid">
            <label className="field business-input-card">
              <span>長文・資料テキスト</span>
              <textarea value={summaryInput} onChange={(event) => setSummaryInput(event.target.value)} placeholder="要約したい文章を貼り付け" rows={12} />
            </label>
            <article className="business-output-card">
              <strong>出力結果</strong>
              {summaryResult ? (
                <div className="business-output-sections">
                  <div><span>3行要約</span><ul>{summaryResult.threeLines.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  <div><span>重要ポイント</span><ul>{summaryResult.points.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  <div><span>アクション</span><ul>{summaryResult.actions.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  <div><span>リスク</span><ul>{summaryResult.risks.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  <div><span>上司向け要約</span><p>{summaryResult.bossSummary}</p></div>
                </div>
              ) : (
                <p className="empty-state">長文を貼ると、共有しやすい要約に整えます。</p>
              )}
            </article>
          </div>
        </section>
      )}

      {activeMode === "reports" && (
        <section className="business-mode-panel" aria-label="日報週報AI">
          <div className="business-mode-heading">
            <div>
              <p className="eyebrow">Report AI</p>
              <h2>日報/週報AI</h2>
              <p>今日やったこと、商談メモ、タスクから、日報・週報・上司向け報告文を作成します。</p>
            </div>
            <div className="mode-action-row">
              <button className="primary-button" type="button" onClick={generateReportMode}>
                <Clipboard size={18} aria-hidden="true" />
                日報を作成
              </button>
              <button className="secondary-button" type="button" onClick={generateReportMode}>
                週報を作成
              </button>
            </div>
          </div>
          <div className="business-mode-grid">
            <label className="field business-input-card">
              <span>今日やったこと・商談メモ・タスク</span>
              <textarea value={reportInput} onChange={(event) => setReportInput(event.target.value)} placeholder="例：午前にReady Crew案件の初回確認、午後に提案書作成、夕方に見積条件を確認。" rows={12} />
            </label>
            <article className="business-output-card">
              <strong>出力結果</strong>
              {reportResult ? (
                <div className="business-output-sections">
                  <div><span>日報</span><ul>{reportResult.daily.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  <div><span>週報</span><ul>{reportResult.weekly.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  <div><span>成果</span><ul>{reportResult.results.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  <div><span>課題</span><ul>{reportResult.issues.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  <div><span>明日の予定</span><ul>{reportResult.tomorrow.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  <div><span>上司向け報告文</span><p>{reportResult.bossMessage}</p></div>
                </div>
              ) : (
                <p className="empty-state">活動メモを貼ると、日報・週報・上司向け報告に整えます。</p>
              )}
            </article>
          </div>
        </section>
      )}

      {activeMode === "sales" && (
      <section className="workspace-grid">
        <form className="input-panel chat-input-panel" onSubmit={handleSubmit}>
          <div className="panel-heading">
            <div>
              <p className="eyebrow">AI Sales Assistant</p>
              <h2>会話で案件を整理</h2>
            </div>
          </div>

          <section className="minimal-input-panel" aria-label="最小入力モード">
            <div className="minimal-input-heading">
              <div>
                <p className="eyebrow">Minimum Input</p>
                <h3>会社名・やりたいこと・困りごとだけで開始</h3>
              </div>
              <button className="primary-button" type="button" onClick={() => organizeMinimalInput(true)}>
                <Sparkles size={18} aria-hidden="true" />
                この内容で生成準備
              </button>
            </div>
            <div className="minimal-input-grid">
              <label className="field">
                <span>会社名</span>
                <input value={minimalInput.companyName} onChange={(event) => updateMinimalField("companyName", event.target.value)} placeholder="例：株式会社サンプル不動産" />
              </label>
              <label className="field">
                <span>やりたいこと</span>
                <input value={minimalInput.goal} onChange={(event) => updateMinimalField("goal", event.target.value)} placeholder="例：Webサイトをリニューアルしたい" />
              </label>
              <label className="field">
                <span>困りごと</span>
                <input value={minimalInput.trouble} onChange={(event) => updateMinimalField("trouble", event.target.value)} placeholder="例：問い合わせが増えない" />
              </label>
            </div>
            <p className="minimal-input-note">未入力項目は「予算：未定」「納期：要確認」「CMS：要確認」「競合：未確認」「決裁者：要確認」「ターゲット：要確認」で仮補完します。</p>
          </section>

          <section className="sales-chat-panel" aria-label="AI営業アシスタント">
            <div className="sales-chat-hero">
              <div className="assistant-avatar">
                <Bot size={22} aria-hidden="true" />
              </div>
              <div>
                <strong>AI営業アシスタント</strong>
                <p>質問に答えるだけで、案件概要・競合情報・見積条件を整理します。</p>
              </div>
            </div>

            <div className="chat-sample-row" aria-label="サンプル案件">
              <button className="sample-button" type="button" onClick={() => loadChatSample("renewal")}>
                Webリニューアル
              </button>
              <button className="sample-button" type="button" onClick={() => loadChatSample("recruit")}>
                採用サイト
              </button>
              <button className="sample-button" type="button" onClick={() => loadChatSample("lp")}>
                LP制作
              </button>
              <button className="sample-button" type="button" onClick={() => loadChatSample("seo")}>
                SEO改善
              </button>
            </div>

            <div className={`chat-ready-card ${chatReadiness.ready ? "is-ready" : ""}`}>
              <MessageCircle size={18} aria-hidden="true" />
              <div>
                <strong>{chatReadiness.ready ? "提案書を生成できます" : "会話で必要情報を整理中"}</strong>
                <p>
                  {chatReadiness.ready
                    ? "不足項目は次回確認事項として扱い、このまま生成へ進めます。"
                    : `最低限必要: ${chatReadiness.missing.join("、") || "入力中"} / 回答 ${chatReadiness.answeredCount}件`}
                </p>
              </div>
            </div>

            <div className="chat-thread" aria-live="polite">
              {chatMessages.map((message) => (
                <div className={`chat-message ${message.role}`} key={message.id}>
                  <span>{message.role === "assistant" ? "AI" : "あなた"}</span>
                  <p>{message.text}</p>
                </div>
              ))}
            </div>

            <div className="chat-compose" aria-label="チャット入力">
              <input
                value={chatDraft}
                onChange={(event) => setChatDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    submitChatAnswer();
                  }
                }}
                placeholder={chatQuestionIndex < chatQuestionFlow.length ? currentChatQuestion.placeholder : "追加情報やヒアリングメモを入力"}
              />
              <button className="icon-button send-button" type="button" onClick={() => submitChatAnswer()} title="送信">
                <Send size={17} aria-hidden="true" />
              </button>
            </div>

            <div className="chat-action-row">
              <button className="secondary-button" type="button" onClick={resetChat}>
                最初から
              </button>
              <button className="primary-button" type="button" onClick={generateFromChatNow} disabled={isLoading || !canGenerate}>
                {isLoading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Sparkles size={18} aria-hidden="true" />}
                {isLoading ? "生成中" : "今の内容で生成する"}
              </button>
            </div>
          </section>

          <div className="input-mode-tabs" aria-label="入力方式">
            <button
              className={inputMode === "easy" ? "is-active" : ""}
              type="button"
              onClick={() => setInputMode("easy")}
            >
              かんたん入力
            </button>
            <button
              className={inputMode === "detail" ? "is-active" : ""}
              type="button"
              onClick={() => setInputMode("detail")}
            >
              詳細入力
            </button>
          </div>

          {inputMode === "easy" && (
            <section className="easy-input-panel" aria-label="かんたん入力">
              <div className="easy-panel-heading">
                <div>
                  <p className="eyebrow">Easy Input</p>
                  <h3>長文を書かずに、まずは最低限だけ入力</h3>
                </div>
                <span>初期表示</span>
              </div>

              <div className="sample-scenario-panel">
                <strong>まずはサンプルで試す</strong>
                <div className="sample-scenario-buttons">
                  <button className="sample-button" type="button" onClick={() => fillSample("renewal")}>
                    Webサイトリニューアル案件
                  </button>
                  <button className="sample-button" type="button" onClick={() => fillSample("recruit")}>
                    採用サイト制作案件
                  </button>
                  <button className="sample-button" type="button" onClick={() => fillSample("lp")}>
                    LP制作案件
                  </button>
                  <button className="sample-button" type="button" onClick={() => fillSample("seo")}>
                    SEO改善案件
                  </button>
                </div>
              </div>

              <div className="minimum-input-box">
                <strong>最低限これだけ入れれば生成できます</strong>
                <p>「何を作りたいか」と「お客様の困りごと」または「目的」を1つ選べば、AI用の案件概要を作れます。</p>
                {easyMissingItems.length > 0 ? (
                  <ul>
                    {easyMissingItems.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <span>最低限の入力は完了しています。</span>
                )}
              </div>

              <div className="easy-field-grid">
                <label className={`field ${!easyInput.projectType.trim() ? "needs-input" : ""}`}>
                  <div className="field-title-row">
                    <span>何を作りたいか</span>
                    <small>必須</small>
                  </div>
                  <input
                    value={easyInput.projectType}
                    onChange={(event) => updateEasyField("projectType", event.target.value)}
                    placeholder="例：コーポレートサイトのリニューアル"
                  />
                </label>

                <label className={`field ${!easyInput.trouble.trim() && easyInput.purposes.length === 0 ? "needs-input" : ""}`}>
                  <div className="field-title-row">
                    <span>お客様の困りごと</span>
                    <small>目的を選べば任意</small>
                  </div>
                  <textarea
                    value={easyInput.trouble}
                    onChange={(event) => updateEasyField("trouble", event.target.value)}
                    placeholder="例：現行サイトが古く、問い合わせにつながっていない"
                    rows={4}
                  />
                </label>
              </div>

              <div className="purpose-check-panel">
                <div className="field-title-row">
                  <span>目的</span>
                  <small>チェックボックスで選択</small>
                </div>
                <div className="purpose-check-grid">
                  {purposeOptions.map((purpose) => (
                    <label className="purpose-check" key={purpose}>
                      <input
                        type="checkbox"
                        checked={easyInput.purposes.includes(purpose)}
                        onChange={() => toggleEasyPurpose(purpose)}
                      />
                      <span>{purpose}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="easy-select-grid">
                <label className="field">
                  <div className="field-title-row">
                    <span>予算</span>
                    <small>任意</small>
                  </div>
                  <select value={easyInput.budget} onChange={(event) => updateEasyField("budget", event.target.value)}>
                    {budgetOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <div className="field-title-row">
                    <span>納期</span>
                    <small>任意</small>
                  </div>
                  <select value={easyInput.deadline} onChange={(event) => updateEasyField("deadline", event.target.value)}>
                    {deadlineOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <div className="field-title-row">
                    <span>CMS希望</span>
                    <small>任意</small>
                  </div>
                  <select value={easyInput.cms} onChange={(event) => updateEasyField("cms", event.target.value)}>
                    {cmsOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="easy-field-grid">
                <label className="field">
                  <div className="field-title-row">
                    <span>競合サイトURL</span>
                    <small>任意</small>
                  </div>
                  <input
                    value={easyInput.competitorSiteUrl}
                    onChange={(event) => updateEasyField("competitorSiteUrl", event.target.value)}
                    placeholder="https://example.com"
                  />
                </label>
                <label className="field">
                  <div className="field-title-row">
                    <span>既存サイトURL</span>
                    <small>任意</small>
                  </div>
                  <input
                    value={easyInput.currentSiteUrl}
                    onChange={(event) => updateEasyField("currentSiteUrl", event.target.value)}
                    placeholder="https://example.co.jp"
                  />
                </label>
                <label className="field easy-field-wide">
                  <div className="field-title-row">
                    <span>決裁者・確認者</span>
                    <small>任意</small>
                  </div>
                  <input
                    value={easyInput.decisionMakers}
                    onChange={(event) => updateEasyField("decisionMakers", event.target.value)}
                    placeholder="例：代表取締役、営業部長、人事責任者"
                  />
                </label>
              </div>

              <div className="organized-preview">
                <strong>AI用に整理された案件概要</strong>
                <p>{form.project_brief.trim() ? "整理済みです。必要なら詳細入力で編集できます。" : "まだ整理されていません。「入力内容を整理」を押すと案件概要欄へ文章化します。"}</p>
              </div>
            </section>
          )}

          <section className="check-panel" aria-label="入力内容チェック">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Pre Check</p>
                <h3>入力内容の不足チェック</h3>
              </div>
              <span className={`decision-pill rank-${dealEvaluation.rank.toLowerCase()}`}>
                {dealEvaluation.rank} / {dealEvaluation.probability}%
              </span>
            </div>
            <div className="check-grid">
              {infoChecks.map((item) => (
                <div className={`check-item ${item.found ? "is-found" : "is-missing"}`} key={item.key}>
                  <span className="check-dot">{item.found ? "OK" : "要確認"}</span>
                  <strong>{item.label}</strong>
                </div>
              ))}
            </div>
            {missingItems.length > 0 && (
              <div className="warning-box">
                <AlertCircle size={18} aria-hidden="true" />
                <div>
                  <strong>次回確認事項</strong>
                  <p className="warning-lead">不足があっても生成できます。精度を上げる場合は、以下の欄へ追記してください。</p>
                  <ul>
                    {missingItems.map((item) => (
                      <li className="missing-guidance-item" key={item.key}>
                        <strong>{item.label}</strong>
                        <span>追記先: {item.targetField}</span>
                        <small>{item.nextQuestion}</small>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </section>

          <section className="plan-panel" aria-label="提案前プラン">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">/plan</p>
                <h3>提案前プラン</h3>
              </div>
              <span className="decision-pill rank-b">生成前整理</span>
            </div>
            <div className="plan-grid">
              <article className="plan-card">
                <strong>入力情報</strong>
                <ul>
                  {proposalPlan.inputInfo.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="plan-card">
                <strong>出力内容</strong>
                <ul>
                  {proposalPlan.outputs.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="plan-card">
                <strong>AIが担当する範囲</strong>
                <ul>
                  {proposalPlan.aiScope.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="plan-card">
                <strong>人間が確認する範囲</strong>
                <ul>
                  {proposalPlan.humanScope.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            </div>
          </section>

          {inputMode === "detail" && (
            <>
          <section className="hearing-panel" aria-label="ヒアリングシート">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Hearing Sheet</p>
                <h3>ヒアリングシート</h3>
              </div>
              <span className={`decision-pill ${hearingQuestionCount > 0 ? "rank-c" : "rank-a"}`}>
                質問 {hearingQuestionCount}件
              </span>
            </div>
            <div className="hearing-list">
              {hearingSheet.map((item) => (
                <article className={`hearing-item ${item.found ? "is-found" : "is-missing"}`} key={item.key}>
                  <div className="hearing-item-header">
                    <strong>{item.category}</strong>
                    <span>{item.found ? "確認済み" : "要確認"}</span>
                  </div>
                  <p>{item.summary}</p>
                  {item.questions.length > 0 && (
                    <ul>
                      {item.questions.map((question) => (
                        <li key={question}>Q. {question}</li>
                      ))}
                    </ul>
                  )}
                </article>
              ))}
            </div>
          </section>

          <label className="field">
            <div className="field-title-row">
              <span>案件概要</span>
              <small>何を書けばいい？ 目的・予算・納期・既存URL・競合があると精度が上がります。</small>
            </div>
            <textarea
              required
              minLength={20}
              value={form.project_brief}
              onChange={(event) => updateField("project_brief", event.target.value)}
              placeholder="Ready Crewから届いた案件概要を貼り付けてください。"
              rows={10}
            />
          </label>

          <label className="field">
            <div className="field-title-row">
              <span>提案先企業情報</span>
              <small>企業名、業種、担当者、決裁者、既存サイトURLを書きます。</small>
            </div>
            <textarea
              value={form.client_company_info}
              onChange={(event) => updateField("client_company_info", event.target.value)}
              placeholder="企業名、業種、事業内容、既存サイトURLなど"
              rows={4}
            />
          </label>

          <label className="field">
            <div className="field-title-row">
              <span>ヒアリング結果</span>
              <small>決定事項、未決事項、次回確認事項をメモのまま貼り付けます。</small>
            </div>
            <textarea
              value={form.hearing_result}
              onChange={(event) => updateField("hearing_result", event.target.value)}
              placeholder="商談メモ、ヒアリング結果、決まったこと、未確認事項などを貼り付けてください。"
              rows={7}
            />
          </label>

          <section className="meeting-panel" aria-label="ヒアリング結果整理">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Meeting Notes</p>
                <h3>ヒアリング結果整理</h3>
              </div>
              <span className={`decision-pill ${hearingResultSummary.hasInput ? "rank-a" : "rank-d"}`}>
                {hearingResultSummary.hasInput ? "生成済み" : "未入力"}
              </span>
            </div>
            <div className="meeting-summary-grid">
              <article className="meeting-summary-card">
                <strong>議事録</strong>
                <ul>
                  {hearingResultSummary.minutes.slice(0, 4).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="meeting-summary-card">
                <strong>決定事項</strong>
                <ul>
                  {hearingResultSummary.decisions.slice(0, 4).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="meeting-summary-card">
                <strong>未決事項</strong>
                <ul>
                  {hearingResultSummary.unresolved.slice(0, 4).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="meeting-summary-card">
                <strong>次回確認事項</strong>
                <ul>
                  {hearingResultSummary.nextConfirmations.slice(0, 4).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            </div>
          </section>

          <div className="field-grid">
            <label className="field">
              <div className="field-title-row">
                <span>競合企業名</span>
                <small>比較されやすい会社名</small>
              </div>
              <textarea
                value={form.competitor_company_name}
                onChange={(event) => updateField("competitor_company_name", event.target.value)}
                placeholder="比較対象の企業名、サービス名など"
                rows={2}
              />
            </label>

            <label className="field">
              <div className="field-title-row">
                <span>競合サイトURL</span>
                <small>公開ページのみ。ログイン操作は想定しません。</small>
              </div>
              <textarea
                value={form.competitor_site_url}
                onChange={(event) => updateField("competitor_site_url", event.target.value)}
                placeholder="https://example.com"
                rows={2}
              />
            </label>
          </div>

          <section className="competitor-panel" aria-label="競合分析支援">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Competitor</p>
                <h3>競合分析支援</h3>
              </div>
              <span className={`decision-pill ${infoChecks.find((item) => item.key === "competitor")?.found ? "rank-a" : "rank-c"}`}>
                {infoChecks.find((item) => item.key === "competitor")?.found ? "競合あり" : "未確認"}
              </span>
            </div>
            <div className="winning-strategy">
              <span>勝ち筋</span>
              <strong>{winningStrategy}</strong>
            </div>
            <div className="competitor-point-grid">
              {competitorPoints.map((item) => (
                <div className="competitor-point" key={item.label}>
                  <strong>{item.label}</strong>
                  <p>{item.point}</p>
                </div>
              ))}
            </div>
            <div className="browser-use-box">
              <div className="browser-use-header">
                <div>
                  <span>Browser Use活用想定</span>
                  <strong>{browserUsePlan.status}</strong>
                </div>
                <small>{browserUsePlan.target}</small>
              </div>
              <div className="browser-use-grid">
                <div>
                  <strong>確認観点</strong>
                  <ul>
                    {browserUsePlan.checks.slice(0, 6).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <strong>安全ルール</strong>
                  <ul>
                    {browserUsePlan.safety.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </section>

          <section className="estimate-input-panel" aria-label="見積条件入力">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Estimate</p>
                <h3>見積条件</h3>
              </div>
              <span className="decision-pill rank-b">{estimateSummary.pageCount}ページ想定</span>
            </div>
            <div className="estimate-field-grid">
              <label className="field">
                <span>想定ページ数</span>
                <input
                  value={form.estimated_page_count}
                  onChange={(event) => updateField("estimated_page_count", event.target.value)}
                  placeholder="例：12ページ"
                />
              </label>
              <label className="field">
                <span>CMS有無</span>
                <input
                  value={form.cms_required}
                  onChange={(event) => updateField("cms_required", event.target.value)}
                  placeholder="あり / なし / 未定"
                />
              </label>
              <label className="field">
                <span>問い合わせフォーム有無</span>
                <input
                  value={form.contact_form_required}
                  onChange={(event) => updateField("contact_form_required", event.target.value)}
                  placeholder="あり / なし / 未定"
                />
              </label>
              <label className="field">
                <span>特殊機能有無</span>
                <input
                  value={form.special_function_required}
                  onChange={(event) => updateField("special_function_required", event.target.value)}
                  placeholder="物件検索、予約、会員機能など"
                />
              </label>
              <label className="field">
                <span>SEO対策有無</span>
                <input
                  value={form.seo_required}
                  onChange={(event) => updateField("seo_required", event.target.value)}
                  placeholder="あり / なし / 初期設計のみ"
                />
              </label>
              <label className="field">
                <span>撮影・原稿作成有無</span>
                <input
                  value={form.content_creation_required}
                  onChange={(event) => updateField("content_creation_required", event.target.value)}
                  placeholder="撮影あり、原稿作成一部あり など"
                />
              </label>
              <label className="field">
                <span>公開希望時期</span>
                <input
                  value={form.desired_launch_timing}
                  onChange={(event) => updateField("desired_launch_timing", event.target.value)}
                  placeholder="例：9月公開希望"
                />
              </label>
              <label className="field">
                <span>予算感</span>
                <input
                  value={form.budget_range}
                  onChange={(event) => updateField("budget_range", event.target.value)}
                  placeholder="例：300万〜500万円"
                />
              </label>
            </div>
          </section>

          <section className="estimate-panel" aria-label="概算見積AI">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Estimate AI</p>
                <h3>概算見積レンジ</h3>
              </div>
              <span
                className={`decision-pill ${
                  estimateSummary.budgetFit === "予算内"
                    ? "rank-a"
                    : estimateSummary.budgetFit === "予算超過の可能性あり"
                      ? "rank-c"
                      : "rank-b"
                }`}
              >
                {estimateSummary.budgetFit}
              </span>
            </div>
            <div className="estimate-total">
              <span>合計概算</span>
              <strong>{estimateSummary.totalLabel}</strong>
              <small>予算感: {estimateSummary.budgetLabel}</small>
            </div>
            <div className="estimate-line-list">
              {estimateSummary.lines.map((line) => (
                <div className={line.enabled ? "estimate-line" : "estimate-line muted"} key={line.name}>
                  <span>{line.name}</span>
                  <strong>{formatEstimateRange(line)}</strong>
                </div>
              ))}
            </div>
            <div className="priority-columns">
              <div>
                <strong>必須対応</strong>
                <p>{estimateSummary.required.join("、") || "次回確認"}</p>
              </div>
              <div>
                <strong>推奨対応</strong>
                <p>{estimateSummary.recommended.join("、") || "次回確認"}</p>
              </div>
              <div>
                <strong>オプション対応</strong>
                <p>{estimateSummary.optional.join("、") || "次回確認"}</p>
              </div>
            </div>
          </section>

          <label className="field">
            <span>自社サービス情報</span>
            <textarea
              value={form.own_service_info}
              onChange={(event) => updateField("own_service_info", event.target.value)}
              placeholder="制作範囲、得意領域、運用支援、CMS構築など"
              rows={4}
            />
          </label>

          <label className="field">
            <span>過去提案書テンプレート</span>
            <textarea
              value={form.past_proposal_template}
              onChange={(event) => updateField("past_proposal_template", event.target.value)}
              placeholder="よく使う構成、言い回し、会社紹介の型など"
              rows={4}
            />
          </label>

          <label className="field">
            <span>成功事例データ</span>
            <textarea
              value={form.case_studies}
              onChange={(event) => updateField("case_studies", event.target.value)}
              placeholder="類似業界、類似課題、成果、制作内容など"
              rows={4}
            />
          </label>

          <section className="deal-panel" aria-label="案件ランク判定">
            <p className="eyebrow">Deal Rank</p>
            <div className="deal-score-row">
              <strong>受注確率</strong>
              <span>{dealEvaluation.probability}%</span>
            </div>
            <div className="risk-summary-row">
              <span>受注リスク</span>
              <strong aria-label={`受注リスク ${dealEvaluation.riskScore} / 5`}>{dealEvaluation.riskLabel}</strong>
            </div>
            <div className="probability-uplift">
              受注確率向上予測 <strong>{dealEvaluation.probability}% → {dealEvaluation.projectedProbability}%</strong>
            </div>
            <p>{dealEvaluation.reason}</p>
            <div className="mini-factor-grid">
              <div>
                <strong>リスク要因</strong>
                <ul>
                  {dealEvaluation.negatives.slice(0, 3).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <strong>改善アクション</strong>
                <ul>
                  {dealEvaluation.improvementActions.slice(0, 3).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="decision-box">{dealEvaluation.decision}</div>
          </section>

          <section className="workflow-panel" aria-label="業務改善連携構想">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Workflow Concept</p>
                <h3>将来の自動化・連携構想</h3>
              </div>
              <span className="decision-pill rank-b">企画表示</span>
            </div>
            <div className="concept-grid">
              {[automationConcept, mcpConcept].map((block) => (
                <article className="concept-card" key={block.title}>
                  <div className="concept-card-header">
                    <strong>{block.title}</strong>
                    <span>{block.label}</span>
                  </div>
                  <ul>
                    {block.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
            <p className="safe-note">
              この表示は業務改善コースの活用想定です。外部サービス連携、自動巡回、機密情報参照はまだ実行しません。
            </p>
          </section>
            </>
          )}

          <section className="generate-flow-panel" aria-label="生成までの流れ">
            <div>
              <span>1</span>
              <strong>まずはサンプルで試す</strong>
              <p>3種類のサンプルから近い案件を選べます。</p>
            </div>
            <div>
              <span>2</span>
              <strong>入力内容を整理</strong>
              <p>かんたん入力をAI用の案件概要に変換します。</p>
              <button className="secondary-button" type="button" onClick={organizeEasyInput} disabled={!canOrganizeEasyInput}>
                入力内容をAI用に整理
              </button>
            </div>
            <div>
              <span>3</span>
              <strong>提案書を生成</strong>
              <p>整理済みの内容からMarkdown・PPTX・PDFを作成します。</p>
              <button className="primary-button" type="submit" disabled={!canSubmit || !canGenerate}>
                {isLoading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Sparkles size={18} aria-hidden="true" />}
                {isLoading ? "生成中" : "提案書を生成"}
              </button>
            </div>
          </section>

          {!canSubmit && !isLoading && (
            <p className="submit-help">かんたん入力では「入力内容をAI用に整理」を押すと生成できます。詳細入力では案件概要を20文字以上入力してください。</p>
          )}

          {errorAdvice && (
            <StatusMessage type="error" title={errorAdvice.title}>
                <p><b>原因:</b> {errorAdvice.cause}</p>
                <p><b>対処:</b> {errorAdvice.action}</p>
                <small>{errorAdvice.detail}</small>
                <div className="error-action-row">
                  {lastDownloadRetry && result && (
                    <button className="secondary-button" type="button" onClick={() => void retryLastDownload()}>
                      再試行
                    </button>
                  )}
                  {/認証|ログイン/.test(errorAdvice.title + errorAdvice.cause) && (
                    <button className="secondary-button" type="button" onClick={() => window.location.reload()}>
                      再ログイン
                    </button>
                  )}
                  {/OpenAI|API制限|制限/.test(errorAdvice.title + errorAdvice.cause) && (
                    <span className="mock-mode-hint">モックモードで試す場合はBackendの USE_MOCK_AI=true にしてください。</span>
                  )}
                </div>
            </StatusMessage>
          )}
        </form>

        <section className="result-panel" aria-label="生成結果">
          <section className="live-brief-panel" aria-label="現在整理された案件概要">
            <div className="live-brief-header">
              <div>
                <p className="eyebrow">Live Brief</p>
                <h2>現在整理された案件概要</h2>
              </div>
              <span className={`decision-pill ${chatReadiness.ready ? "rank-a" : "rank-c"}`}>
                {chatReadiness.ready ? "生成可能" : "整理中"}
              </span>
            </div>
            <div className="win-prediction-card">
              <div>
                <span>AI受注予測</span>
                <strong>{dealEvaluation.riskLabel}</strong>
              </div>
              <div>
                <span>受注確率</span>
                <strong>{dealEvaluation.probability}%</strong>
              </div>
              <ul>
                {dealEvaluation.positives.slice(0, 3).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="live-brief-grid">
              {liveProjectSummary.map((section) => (
                <article className="live-brief-card" key={section.title}>
                  <strong>{section.title}</strong>
                  <ul>
                    {section.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
            <div className="live-status-row">
              <div>
                <span>受注確率</span>
                <strong>{dealEvaluation.probability}%</strong>
              </div>
              <div>
                <span>予算適合</span>
                <strong>{estimateSummary.budgetFit}</strong>
              </div>
              <div>
                <span>競合分析</span>
                <strong>{form.competitor_site_url.trim() || form.competitor_company_name.trim() ? "反映済み" : "未確認"}</strong>
              </div>
            </div>
            <div className="recommendation-panel">
              <div className="opportunity-card">
                <span>案件化しやすさ</span>
                <strong>{salesOpportunityScore.stars}</strong>
                <p>{salesOpportunityScore.reasons.slice(0, 2).join(" / ")}</p>
              </div>
              <div className="recommendation-list">
                <strong>この案件ならこんな提案が刺さります</strong>
                <ol>
                  {aiRecommendations.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ol>
              </div>
            </div>
            <div className="strategy-grid" aria-label="AI提案戦略">
              {strategyCards.map((strategy) => (
                <article className="strategy-card" key={strategy.title}>
                  <span>AI提案戦略</span>
                  <strong>{strategy.title}</strong>
                  <p>{strategy.reason}</p>
                </article>
              ))}
            </div>
            <section className="preview-panel" aria-label="PowerPoint風プレビュー">
              <div className="preview-heading">
                <div>
                  <p className="eyebrow">Preview</p>
                  <h3>提案書プレビュー</h3>
                </div>
                <span>{editablePreviewSlides.length} slides</span>
              </div>
              <div className="preview-slide-grid">
                {editablePreviewSlides.map((slide, index) => (
                  <article className="preview-slide" key={`${slide.title}-${index}`}>
                    <span>{index + 1}</span>
                    <input
                      value={slide.title}
                      onChange={(event) => updatePreviewSlide(index, "title", event.target.value)}
                      aria-label={`スライド${index + 1}タイトル`}
                    />
                    <textarea
                      value={slide.body}
                      onChange={(event) => updatePreviewSlide(index, "body", event.target.value)}
                      aria-label={`スライド${index + 1}本文`}
                      rows={4}
                    />
                  </article>
                ))}
              </div>
            </section>
          </section>

          <div className="panel-heading">
            <div>
              <p className="eyebrow">Output</p>
              <h2>生成結果</h2>
            </div>
            <div className="toolbar">
              <button className="icon-button" type="button" onClick={copyMarkdown} disabled={!result} title="Markdownをコピー">
                <Clipboard size={18} aria-hidden="true" />
              </button>
              <button className="icon-button" type="button" onClick={() => downloadMarkdown()} disabled={!result} title="Markdownをダウンロード">
                <Download size={18} aria-hidden="true" />
              </button>
            </div>
          </div>

          {copyState === "copied" && <p className="copy-note">Markdownをコピーしました。</p>}

          {!result && !isLoading && (
            <div className="empty-state">
              <FileText size={40} aria-hidden="true" />
              <p>案件概要を入力して生成すると、提案書初稿がここに表示されます。</p>
            </div>
          )}

          {isLoading && (
            <div className="loading-state" aria-live="polite">
              <Loader2 className="spin" size={42} aria-hidden="true" />
              <strong>提案書初稿を生成しています</strong>
              <p>入力内容をもとに、営業提案で使える叩き台を整理しています。</p>
              <div className="progress-steps">
                <div className="is-active">
                  <span>1</span>
                  <strong>案件分析中</strong>
                  <small>目的・課題・不足情報を確認</small>
                </div>
                <div>
                  <span>2</span>
                  <strong>提案構成作成中</strong>
                  <small>ストーリーと章立てを整理</small>
                </div>
                <div>
                  <span>3</span>
                  <strong>資料生成準備中</strong>
                  <small>PPTX・PDF出力データを準備</small>
                </div>
              </div>
            </div>
          )}

          {result && (
            <div className="output-layout">
              <section className="output-summary-panel" aria-label="生成結果サマリー">
                {outputDigest.map((section) => (
                  <article className="output-summary-card" key={section.title}>
                    <strong>{section.title}</strong>
                    <ul>
                      {section.items.slice(0, 4).map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </article>
                ))}
              </section>

              <article className="markdown-preview">
                <pre>{displayedMarkdown}</pre>
              </article>

              <aside className="ppt-panel">
                <p className="eyebrow">営業評価</p>
                <div className="rating-stack">
                  <div className={`rank-card rank-${displayedWin.rank.toLowerCase()}`}>
                    <span>受注確率</span>
                    <strong>{displayedProbability}%</strong>
                    <small>{displayedWin.rank}ランク / {displayedWin.label}</small>
                  </div>
                  <div className={`metric-card rank-${displayedWin.rank.toLowerCase()}`}>
                    <span>受注リスク</span>
                    <strong className="risk-stars">{displayedWin.riskLabel}</strong>
                    <small>{displayedWin.riskScore} / 5</small>
                  </div>
                  <div className={`metric-card rank-${displayedWin.rank.toLowerCase()}`}>
                    <span>受注確率向上予測</span>
                    <strong>{displayedWin.probability}% → {displayedWin.projectedProbability}%</strong>
                    <small>改善アクション実施後</small>
                  </div>
                  {salesIndicators.map((indicator) => (
                    <div className={`metric-card rank-${indicator.rank.toLowerCase()}`} key={indicator.title}>
                      <span>{indicator.title}</span>
                      <strong>{indicator.rank}</strong>
                      <small>{indicator.label}</small>
                    </div>
                  ))}
                </div>
                <p className="rank-reason">{displayedWin.reason}</p>

                <div className="factor-grid">
                  <div>
                    <strong>リスク要因</strong>
                    <ul>
                      {displayedWin.riskFactors.slice(0, 3).map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <strong>改善アクション</strong>
                    <ul>
                      {displayedWin.improvementActions.slice(0, 3).map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                <div className="decision-box">{dealEvaluation.decision}</div>

                <div className="next-action-panel">
                  <strong>次にやること</strong>
                  <ol>
                    <li>内容を確認</li>
                    <li>不足情報を追記</li>
                    <li>PowerPointをダウンロード</li>
                    <li>人が最終確認して提出</li>
                  </ol>
                </div>

                <section className="ai-quality-panel" aria-label="AI品質チェック">
                  <div className="quality-total">
                    <span>AI品質チェック</span>
                    <strong>{qualityScore.total}点</strong>
                    <small>100点満点</small>
                  </div>
                  <div className="quality-grid">
                    <div><span>提案力</span><strong>{qualityScore.proposal}</strong></div>
                    <div><span>説得力</span><strong>{qualityScore.persuasion}</strong></div>
                    <div><span>ROI</span><strong>{qualityScore.roi}</strong></div>
                    <div><span>差別化</span><strong>{qualityScore.differentiation}</strong></div>
                    <div><span>読みやすさ</span><strong>{qualityScore.readability}</strong></div>
                  </div>
                  <ul>
                    {qualityScore.improvements.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </section>

                <section className="ai-assist-output-panel" aria-label="AI追加支援">
                  <button className="secondary-button" type="button" onClick={() => setShowEmailDraft((current) => !current)}>
                    <Mail size={16} aria-hidden="true" />
                    提案書送付メールを作る
                  </button>
                  {showEmailDraft && (
                    <div className="draft-box">
                      <strong>件名</strong>
                      <p>{draftEmail.subject}</p>
                      <strong>本文</strong>
                      <p>{draftEmail.body}</p>
                      <strong>署名</strong>
                      <p>{draftEmail.signature}</p>
                    </div>
                  )}
                  <button className="secondary-button" type="button" onClick={() => setShowMinutes((current) => !current)}>
                    <FileCheck2 size={16} aria-hidden="true" />
                    AI議事録を作る
                  </button>
                  {showMinutes && (
                    <div className="draft-box">
                      <strong>議事録</strong>
                      <ul>{aiMinutes.minutes.map((item) => <li key={item}>{item}</li>)}</ul>
                      <strong>ToDo</strong>
                      <ul>{aiMinutes.todos.map((item) => <li key={item}>{item}</li>)}</ul>
                      <strong>次回アクション</strong>
                      <ul>{aiMinutes.nextActions.map((item) => <li key={item}>{item}</li>)}</ul>
                    </div>
                  )}
                </section>

                <section className="win-improvement-panel" aria-label="AI改善提案">
                  <strong>もっとこうすると受注率が上がります</strong>
                  <ul>
                    {winRateImprovements.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </section>

                <section className="similar-case-panel" aria-label="似ている過去案件">
                  <strong>似ている過去案件</strong>
                  {similarCases.length ? (
                    similarCases.map(({ entry, score }) => (
                      <button className="similar-case-button" type="button" key={entry.id} onClick={() => restoreHistory(entry)}>
                        <span>{entry.clientName}</span>
                        <small>類似度 {score} / 再利用</small>
                      </button>
                    ))
                  ) : (
                    <p>生成履歴が増えると、似ている案件をここに表示します。</p>
                  )}
                </section>

                <p className="eyebrow">Export</p>
                <h3>{result.powerpoint_generation_data.deck_title}</h3>
                <p className="ppt-help">おすすめ順に並べています。まずは要約版で共有し、必要に応じて詳細版と見積書を確認します。</p>
                <div className="ppt-button-stack">
                  <button
                    className="ppt-download-button summary"
                    type="button"
                    onClick={downloadSummaryPowerPoint}
                    disabled={!result || !canGenerate || isDownloadingPowerPoint || isDownloadingSummaryPowerPoint || isDownloadingEstimatePdf}
                  >
                    {isDownloadingSummaryPowerPoint ? (
                      <Loader2 className="spin" size={18} aria-hidden="true" />
                    ) : (
                      <FileDown size={18} aria-hidden="true" />
                    )}
                    <span>
                      <strong>{isDownloadingSummaryPowerPoint ? "要約版生成中" : "要約PowerPoint"}</strong>
                      <small>発表用</small>
                    </span>
                  </button>
                  <button
                    className="ppt-download-button"
                    type="button"
                    onClick={downloadPowerPoint}
                    disabled={!result || !canGenerate || isDownloadingPowerPoint || isDownloadingSummaryPowerPoint || isDownloadingEstimatePdf}
                  >
                    {isDownloadingPowerPoint ? (
                      <Loader2 className="spin" size={18} aria-hidden="true" />
                    ) : (
                      <FileDown size={18} aria-hidden="true" />
                    )}
                    <span>
                      <strong>{isDownloadingPowerPoint ? "生成中" : "通常PowerPoint"}</strong>
                      <small>詳細提案用</small>
                    </span>
                  </button>
                  <button
                    className="ppt-download-button pdf"
                    type="button"
                    onClick={downloadEstimatePdfCurrent}
                    disabled={!result || !canGenerate || isDownloadingPowerPoint || isDownloadingSummaryPowerPoint || isDownloadingEstimatePdf}
                  >
                    {isDownloadingEstimatePdf ? (
                      <Loader2 className="spin" size={18} aria-hidden="true" />
                    ) : (
                      <FileDown size={18} aria-hidden="true" />
                    )}
                    <span>
                      <strong>{isDownloadingEstimatePdf ? "PDF生成中" : "見積書PDF"}</strong>
                      <small>見積確認用</small>
                    </span>
                  </button>
                  <button className="ppt-download-button markdown" type="button" onClick={() => downloadMarkdown()}>
                    <Download size={18} aria-hidden="true" />
                    <span>
                      <strong>Markdown</strong>
                      <small>原稿確認用</small>
                    </span>
                  </button>
                </div>
                <div className="slide-list">
                  {result.powerpoint_generation_data.slides.map((slide) => (
                    <div className="slide-row" key={slide.slide_no}>
                      <span>{slide.slide_no}</span>
                      <p>{slide.title}</p>
                    </div>
                  ))}
                </div>
              </aside>
            </div>
          )}

          <section className="history-panel" aria-label="生成履歴">
            <div className="history-heading">
              <div>
                <p className="eyebrow">History</p>
                <h3>生成履歴</h3>
              </div>
              <button className="text-button" type="button" onClick={clearHistory} disabled={history.length === 0}>
                履歴を削除
              </button>
            </div>
            {history.length === 0 ? (
              <p className="history-empty">生成した案件はここにローカル保存されます。</p>
            ) : (
              <div className="history-list">
                {history.map((entry) => (
                  <article className="history-item" key={entry.id}>
                    <div>
                      <span>{formatDateTime(entry.createdAt)}</span>
                      <strong>{entry.clientName}</strong>
                      <p>{entry.title}</p>
                    </div>
                    <div className="history-actions">
                      <button className="icon-button subtle" type="button" onClick={() => restoreHistory(entry)} title="この履歴を開く">
                        <RotateCcw size={16} aria-hidden="true" />
                      </button>
                      <button className="icon-button subtle" type="button" onClick={() => downloadMarkdown(entry.result, entry.form)} title="Markdownを再ダウンロード">
                        <History size={16} aria-hidden="true" />
                      </button>
                      <button
                        className="icon-button subtle"
                        type="button"
                        onClick={() => downloadPowerPointFor(entry.result, entry.form, false)}
                        title="詳細PowerPointを再ダウンロード"
                      >
                        <FileDown size={16} aria-hidden="true" />
                      </button>
                      <button
                        className="icon-button subtle"
                        type="button"
                        onClick={() => downloadPowerPointFor(entry.result, entry.form, true)}
                        title="要約PowerPointを再ダウンロード"
                      >
                        <Download size={16} aria-hidden="true" />
                      </button>
                      <button
                        className="icon-button subtle"
                        type="button"
                        onClick={() => downloadEstimatePdfFor(entry.result, entry.form)}
                        title="見積書PDFを再ダウンロード"
                      >
                        <FileDown size={16} aria-hidden="true" />
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </section>
      </section>

      )}

      <section className="future-integration-panel" aria-label="今後の拡張予定">
        <div className="section-heading">
          <p className="eyebrow">Roadmap</p>
          <h2>今後の拡張予定</h2>
          <p>現時点では実連携せず、今後MCPで社内データや外部サービスと安全に連携する構想です。</p>
        </div>
        <div className="future-card-grid">
          {[
            "Google Drive連携",
            "Gmail/Outlook連携",
            "Googleカレンダー連携",
            "Slack/Teams連携",
            "kintone/HubSpot/Salesforce連携",
            "社内FAQ/RAG連携"
          ].map((item) => (
            <article key={item}>
              <strong>{item}</strong>
              <p>今後MCPで連携予定</p>
            </article>
          ))}
        </div>
      </section>

      {isConfirmOpen && (
        <div className="confirm-overlay" role="dialog" aria-modal="true" aria-label="生成前確認">
          <div className="confirm-modal">
            <div className="confirm-header">
              <div>
                <p className="eyebrow">Confirm</p>
                <h2>生成前の確認</h2>
              </div>
              <button className="icon-button" type="button" onClick={() => setIsConfirmOpen(false)} title="閉じる">
                <X size={18} aria-hidden="true" />
              </button>
            </div>

            <div className="confirm-easy-lead">
              <strong>この内容で生成できます</strong>
              <p>未入力項目は「未定」「要確認」「競合未確認」として扱い、次回確認事項へ反映します。</p>
            </div>

            <div className="confirm-card-grid">
              {preGenerateCards.map((item) => (
                <article className="confirm-card" key={item.label}>
                  <span>{item.label}</span>
                  <p>{item.value}</p>
                </article>
              ))}
            </div>

            <div className={`confirm-rank rank-${dealEvaluation.rank.toLowerCase()}`}>
              <strong>{dealEvaluation.rank}ランク / 受注確率 {dealEvaluation.probability}%</strong>
              <span>{dealEvaluation.decision}</span>
            </div>

            {missingItems.length > 0 && (
              <div className="warning-box">
                <AlertCircle size={18} aria-hidden="true" />
                <div>
                  <strong>不足情報があります。生成は可能ですが、次回確認事項として反映します。</strong>
                  <p className="warning-lead">提案精度を上げる場合は、以下の欄へ追記してください。</p>
                  <ul>
                    {missingItems.map((item) => (
                      <li className="missing-guidance-item" key={item.key}>
                        <strong>{item.label}</strong>
                        <span>追記先: {item.targetField}</span>
                        <small>{item.nextQuestion}</small>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            <div className="modal-actions">
              <button className="secondary-button" type="button" onClick={() => setIsConfirmOpen(false)}>
                戻って修正
              </button>
              <button className="primary-button confirm-generate-button" type="button" onClick={generateProposal} disabled={!canGenerate}>
                この内容で提案書を生成
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
    </AuthGate>
  );
}
