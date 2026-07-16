import type { AnalysisResponse, ProposalRequest } from "@/types/proposal";

export type Rank = "A" | "B" | "C" | "D";
export type InputMode = "easy" | "detail";
export type SampleKind = "renewal" | "recruit" | "lp" | "seo";
export type ChatRole = "assistant" | "user";
export type ChatAnswerKey = "project" | "company" | "trouble" | "budget" | "deadline" | "competitor";

export type EasyInput = {
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

export type MinimalInput = {
  companyName: string;
  goal: string;
  trouble: string;
};

export type ChatMessage = {
  id: string;
  role: ChatRole;
  text: string;
};

export type ChatQuestion = {
  key: ChatAnswerKey;
  label: string;
  question: string;
  placeholder: string;
};

export type ChatAnswers = Partial<Record<ChatAnswerKey, string>>;
export type SourceTemplateKind = "readyCrew" | "hearing" | "slack";

export type ExtractedInfo = {
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

export type UrlInsight = {
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

export type SalesOpportunityScore = {
  score: number;
  stars: string;
  label: string;
  reasons: string[];
};

export type StrategyCard = {
  title: string;
  reason: string;
};

export type PreviewSlide = {
  title: string;
  body: string;
};

export type QualityScore = {
  total: number;
  proposal: number;
  persuasion: number;
  roi: number;
  differentiation: number;
  readability: number;
  improvements: string[];
};

export type DraftEmail = {
  subject: string;
  body: string;
  signature: string;
};

export type AiMinutes = {
  minutes: string[];
  todos: string[];
  nextActions: string[];
};

export type CoachQuestion = {
  priority: number;
  question: string;
  reason: string;
};

export type MeetingEvaluation = {
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

export type NextMeetingPrep = {
  confirmations: string[];
  homework: string[];
  deliverables: string[];
};

export type DailyReport = {
  activities: string[];
  meeting: string[];
  results: string[];
  issues: string[];
  tomorrow: string[];
};

export type KnowledgeGroups = {
  similar: HistoryEntry[];
  success: HistoryEntry[];
  lost: HistoryEntry[];
};

export type RoleplayScenario = "renewal" | "recruit" | "lp" | "branding";
export type RoleplayMessage = {
  role: "customer" | "sales";
  text: string;
};

export type WorkMode = "sales" | "coach" | "minutes" | "mail" | "tasks" | "faq" | "summary" | "reports";
export type AiEmployeeRole = "secretary" | "sales" | "director" | "writer" | "designer" | "pm";
export type AgentStepStatus = "waiting" | "running" | "done";

export type GeneratedCounts = Record<WorkMode, number>;

export type CompanyResearch = {
  overview: string;
  competitors: string[];
  recruitment: string;
  news: string[];
  services: string[];
  sns: string[];
};

export type DigitalAgentStep = {
  label: string;
  detail: string;
  status: AgentStepStatus;
};

export type AutomationSettings = {
  morning: boolean;
  weekly: boolean;
  deadline: boolean;
};

export type MinutesAiResult = {
  minutes: string[];
  decisions: string[];
  unresolved: string[];
  todos: Array<{ task: string; owner: string; deadline: string }>;
  nextConfirmations: string[];
};

export type MailAiResult = {
  subject: string;
  body: string;
  reply: string;
  polite: string;
  short: string;
};

export type TaskAiResult = {
  tasks: Array<{ task: string; priority: string; owner: string; deadline: string; risk: string }>;
  nextAction: string;
};

export type FaqAiResult = {
  answer: string;
  department: string;
  references: string[];
  notes: string[];
};

export type SummaryAiResult = {
  threeLines: string[];
  points: string[];
  actions: string[];
  risks: string[];
  bossSummary: string;
};

export type ReportAiResult = {
  daily: string[];
  weekly: string[];
  results: string[];
  issues: string[];
  tomorrow: string[];
  bossMessage: string;
};

export type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: (() => void) | null;
  start: () => void;
};

export type GuideStep = 1 | 2 | 3 | 4 | 5;
export type AutoFlowStatus = "idle" | "typing" | "analyzing" | "question" | "reviewing" | "generating" | "complete";

export type SalesIndicator = {
  title: string;
  rank: Rank;
  label: string;
};

export type InfoCheck = {
  key: string;
  label: string;
  found: boolean;
  targetField: string;
  nextQuestion: string;
};

export type HearingSheetCategory = {
  key: string;
  category: string;
  found: boolean;
  summary: string;
  questions: string[];
};

export type HearingResultSummary = {
  hasInput: boolean;
  minutes: string[];
  decisions: string[];
  unresolved: string[];
  nextConfirmations: string[];
};

export type DealEvaluation = {
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

export type CompetitorPoint = {
  label: string;
  point: string;
};

export type EstimatePriority = "必須対応" | "推奨対応" | "オプション対応";

export type EstimateLine = {
  name: string;
  min: number;
  max: number;
  priority: EstimatePriority;
  enabled: boolean;
};

export type EstimateSummary = {
  pageCount: number;
  scopeLabel: string;
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

export type HistoryEntry = {
  id: string;
  createdAt: string;
  title: string;
  clientName: string;
  form: ProposalRequest;
  result: AnalysisResponse;
};

export type ProposalPlan = {
  inputInfo: string[];
  outputs: string[];
  aiScope: string[];
  humanScope: string[];
};

export type BrowserUsePlan = {
  status: string;
  target: string;
  checks: string[];
  safety: string[];
};

export type ConceptBlock = {
  title: string;
  label: string;
  items: string[];
};

export type OutputDigestSection = {
  title: string;
  items: string[];
};

export type ErrorAdvice = {
  title: string;
  cause: string;
  action: string;
  detail: string;
};
