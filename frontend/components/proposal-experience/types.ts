import type { AnalysisResponse } from "@/types/proposal";
import type { PresentationLayoutDecisionRequest, PresentationQualityDownloadReport, PresentationQualityRequestState } from "@/lib/pptx";

export type ProposalExperienceView =
  | "home"
  | "new-proposal"
  | "editor"
  | "history"
  | "projects"
  | "assistant"
  | "templates"
  | "analytics"
  | "improvement"
  | "admin"
  | "settings";

export type PresentationTemplateId =
  | "corporate_clean"
  | "modern_dark"
  | "creative_agency"
  | "executive_minimal"
  | "data_driven"
  | "warm_professional"
  | "japanese_business"
  | "bold_vision";

export type PromptBuilderDraft = {
  projectName: string;
  clientName: string;
  industry: string;
  projectType: string;
  deadline: string;
  business: string;
  targetUsers: string;
  decisionMaker: string;
  stakeholders: string;
  priorities: string;
  currentState: string;
  visibleIssues: string;
  hiddenIssues: string;
  background: string;
  riskIfUnsolved: string;
  budget: string;
  scope: string;
  requiredFeatures: string;
  constraints: string;
  competitors: string;
  appeal: string;
  tone: string;
  deckLength: string;
  designStyle: PresentationTemplateId;
  outputFormat: string;
};

export type StorySlide = {
  id: string;
  title: string;
  purpose: string;
  message: string;
  layout: string;
  diagram: string;
  evidence: string;
  caution: string;
};

export type StoryPlan = {
  storyType: string;
  reason: string;
  decisionMaker: string;
  mainClaim: string;
  flow: string[];
  slides: StorySlide[];
  missingEvidence: string[];
  objections: Array<{ objection: string; response: string }>;
  nextAction: string;
  salesStrategyBrief?: SalesStrategyBrief;
};

export type DecisionMakerProfile = {
  decisionMaker: string;
  focusPoints: string[];
  avoidExpressions: string[];
  proposalOrder: string[];
};

export type SalesStrategyObjection = {
  objection: string;
  reason: string;
  recommendedSlide: string;
  recommendedEvidence: string;
};

export type SalesStrategyRisk = {
  category: "missing" | "hypothesis" | "needs_confirmation" | "ai_inferred" | "provided";
  item: string;
  reason: string;
};

export type EvidenceClassification = {
  missing: string[];
  hypothesis: string[];
  needsConfirmation: string[];
  aiInferred: string[];
};

export type SalesStrategyBrief = {
  schemaVersion: "sales_strategy_brief_v1";
  projectCategory: string;
  customerIndustry: string;
  customerSize: string;
  customerMaturity: string;
  businessModel: string;
  decisionMaker: string;
  decisionProcess: string;
  stakeholders: string[];
  businessGoal: string;
  currentSituation: string;
  painPoints: string[];
  urgency: string;
  budgetStatus: string;
  timeline: string;
  competitiveSituation: string;
  proposalPosition: string;
  winningStrategy: string;
  expectedObjections: SalesStrategyObjection[];
  riskFactors: SalesStrategyRisk[];
  differentiation: string[];
  recommendedStoryType: string;
  recommendedSlideTypes: string[];
  recommendedPresentationTone: string;
  executiveSummary: string;
  confidence: number;
  humanReviewRequired: boolean;
  humanReviewReasons: string[];
  decisionMakerProfile: DecisionMakerProfile;
  evidenceClassification: EvidenceClassification;
  selectionReasons: string[];
};

export type StrategyWorkspaceStatus = "draft" | "review" | "approved";

export type StrategyWorkspaceEditableField =
  | "winningStrategy"
  | "proposalPosition"
  | "decisionMaker"
  | "competitiveSituation"
  | "expectedObjections"
  | "recommendedPresentationTone"
  | "businessGoal"
  | "painPoints"
  | "differentiation"
  | "recommendedStoryType"
  | "recommendedSlideTypes"
  | "executiveSummary";

export type StrategyWorkspaceChange = {
  field: StrategyWorkspaceEditableField;
  aiValue: string;
  editedValue: string;
  changed: boolean;
};

export type StrategyScoreItem = {
  key: string;
  label: string;
  score: number;
  reason: string;
};

export type StrategyWorkspaceScore = {
  total: number;
  items: StrategyScoreItem[];
  changedFieldCount: number;
  confirmedInformationCount: number;
};

export type StoryCandidate = {
  id: string;
  label: string;
  storyType: string;
  reason: string;
  slideTypes: string[];
};

export type ToneCandidate = {
  id: string;
  label: string;
  tone: string;
  summary: string;
};

export type ProposalStrategyWorkspace = {
  schemaVersion: "proposal_strategy_workspace_v1";
  status: StrategyWorkspaceStatus;
  aiBrief: SalesStrategyBrief;
  editedBrief: SalesStrategyBrief;
  selectedStoryId: string;
  selectedTone: string;
  confirmedInformation: string[];
  changes: StrategyWorkspaceChange[];
};

export type PresentationQualityReport = {
  total: number;
  grade: "A" | "B" | "C" | "D";
  items: PresentationQualityCategoryScore[];
  warnings: string[];
  ruleFindings: QualityRuleFinding[];
  diagramRecommendations: DiagramRecommendation[];
  fitRecommendations: ContentFitRecommendation[];
  autoFixSuggestions: AutoFixSuggestion[];
};

export type PresentationQualityCategoryScore = {
  key: string;
  label: string;
  score: number;
  weight: number;
  reason: string;
  improvement: string;
  severity: "ok" | "warning" | "critical";
};

export type QualityRuleFinding = {
  rule: string;
  rule_id?: string;
  category?: string;
  slideId?: string;
  slideTitle?: string;
  severity: "info" | "warning" | "critical";
  message: string;
  recommendation: string;
  auto_fixable?: boolean;
  confidence?: number;
  human_review_required?: boolean;
};

export type DiagramType = "比較表" | "タイムライン" | "ロードマップ" | "KPIカード" | "フロー" | "マトリクス";

export type DiagramRecommendation = {
  slideId: string;
  slideTitle: string;
  diagramType: DiagramType;
  reason: string;
  priority: "high" | "medium" | "low";
};

export type ContentFitRecommendation = {
  slideId: string;
  slideTitle: string;
  action: "圧縮" | "分割" | "図解化";
  reason: string;
  beforeLength: number;
  expectedEffect: string;
};

export type AutoFixSuggestion = {
  id: string;
  slideId: string;
  slideTitle: string;
  type: "title" | "content" | "diagram" | "layout" | "message";
  reason: string;
  before: Pick<StorySlide, "title" | "message" | "layout" | "diagram" | "caution">;
  after: Partial<Pick<StorySlide, "title" | "message" | "layout" | "diagram" | "caution">>;
};

export type ProposalExperienceStudioProps = {
  sourceText: string;
  result: AnalysisResponse | null;
  isGenerating: boolean;
  canGenerate: boolean;
  canDownloadOutputs: boolean;
  canCreateBeautifulAi: boolean;
  selectedTemplate: PresentationTemplateId;
  onTemplateChange: (template: PresentationTemplateId) => void;
  onSourceTextChange: (value: string) => void;
  onGenerate: () => Promise<void> | void;
  onDownloadPowerPoint: (powerpointData?: AnalysisResponse["powerpoint_generation_data"], qualityState?: PresentationQualityRequestState, layoutDecisions?: PresentationLayoutDecisionRequest[]) => Promise<void> | void;
  onDownloadPdf: () => Promise<void> | void;
  onCreateBeautifulAi: () => Promise<void> | void;
  lastPptxQualityReport?: PresentationQualityDownloadReport | null;
};

export const presentationTemplateOptions: Array<{
  id: PresentationTemplateId;
  label: string;
  summary: string;
}> = [
  { id: "corporate_clean", label: "Corporate Clean", summary: "白基調で信頼感を重視" },
  { id: "modern_dark", label: "Modern Dark", summary: "AI・テクノロジー向け" },
  { id: "creative_agency", label: "Creative Agency", summary: "制作・広告・ブランド向け" },
  { id: "executive_minimal", label: "Executive Minimal", summary: "経営層向けに簡潔" },
  { id: "data_driven", label: "Data Driven", summary: "KPIと分析を強調" },
  { id: "warm_professional", label: "Warm Professional", summary: "採用・教育・人材向け" },
  { id: "japanese_business", label: "Japanese Business", summary: "社内稟議に合う落ち着き" },
  { id: "bold_vision", label: "Bold Vision", summary: "新規事業・変革提案向け" }
];
