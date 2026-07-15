"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
  Loader2,
  Mic,
  MessageCircle,
  Send,
  Sparkles,
  UploadCloud,
  X
} from "lucide-react";
import { AuthGate } from "@/components/AuthGate";
import { BeautifulAiStatusCard } from "@/components/BeautifulAiStatusCard";
import { GuidedFlow } from "@/components/guided-flow/GuidedFlow";
import type { BeautifulAiSimpleRequirement, GuidedProgressStage, GuidedSummaryItem } from "@/components/guided-flow/types";
import { WorkspaceProgress, type AiWorkspaceAgentKey } from "@/components/workspace/WorkspaceProgress";
import { WorkspaceSwitcher } from "@/components/WorkspaceSwitcher";
import { AdminReleaseManagementPanel } from "@/components/AdminReleaseManagementPanel";
import { AdminReviewPanel } from "@/components/AdminReviewPanel";
import { CrmPanel } from "@/components/CrmPanel";
import { Dashboard } from "@/components/Dashboard";
import { Header } from "@/components/Header";
import type { HealthSnapshot } from "@/components/HealthStatus";
import { PresentationReviewPanel } from "@/components/PresentationReviewPanel";
import { ProposalOptimizationPanel } from "@/components/ProposalOptimizationPanel";
import { RealOperationsDashboard } from "@/components/dashboard/RealOperationsDashboard";
import { ReleaseUpdatesPanel } from "@/components/ReleaseUpdatesPanel";
import { StatusMessage } from "@/components/ui/StatusMessage";
import { UatModePanel } from "@/components/UatModePanel";
import { AdminSection } from "@/components/app-shell/sections/AdminSection";
import { DigitalCoworkerSection } from "@/components/app-shell/sections/DigitalCoworkerSection";
import { ProposalResultSection } from "@/components/app-shell/sections/ProposalResultSection";
import { SalesInfoSection } from "@/components/app-shell/sections/SalesInfoSection";
import { WorkModeSection } from "@/components/app-shell/sections/WorkModeSection";
import type {
  AiEmployeeRole,
  AutoFlowStatus,
  AutomationSettings,
  ChatAnswers,
  ChatMessage,
  CompanyResearch,
  DailyReport,
  DigitalAgentStep,
  EasyInput,
  ExtractedInfo,
  FaqAiResult,
  GeneratedCounts,
  GuideStep,
  HistoryEntry,
  InputMode,
  MailAiResult,
  MinimalInput,
  MinutesAiResult,
  PreviewSlide,
  ReportAiResult,
  RoleplayMessage,
  RoleplayScenario,
  SampleKind,
  SourceTemplateKind,
  SpeechRecognitionLike,
  SummaryAiResult,
  TaskAiResult,
  UrlInsight,
  WorkMode
} from "@/components/app-shell/types";
import {
  GUIDE_TUTORIAL_KEY,
  HISTORY_KEY,
  MAX_HISTORY_COUNT,
  PILOT_CHECKLIST_KEY,
  emptyFeedbackSummary,
  feedbackRatingLabels,
  initialForm,
  initialPilotFeedbackScores,
  pilotFeedbackQuestions,
  sampleBrief,
  type PilotFeedbackScores
} from "@/components/app-shell/constants";
import {
  analyzeProposal,
  createUser,
  downloadUsageDashboardCsv,
  getAuditLogs,
  getCrm,
  getDbLogs,
  getFeedback,
  getQualityGate,
  completeQualityGate,
  getUsageDashboard,
  getWorkspaceContext,
  getPilotStatus,
  listUsers,
  researchCompanyUrl,
  saveUsageLogToBackend,
  submitFeedback,
  switchWorkspaceContext,
  confirmPilotChecklist,
  updateUserActive,
  updateUserPilot,
  type CrmCustomer,
  type CrmProject,
  type FeedbackEntry,
  type FeedbackRating,
  type FeedbackSummary,
  type ManagedUser,
  type PilotStatus,
  type UsageDashboardData,
  type QualityGateRecord,
  type AuditLog,
  type WorkspaceContext
} from "@/lib/api";
import { getStoredUser, logoutCurrentSession, saveAuthUser, type AuthUser } from "@/lib/auth";
import {
  buildBeautifulAiPayload,
  createBeautifulAiPresentation,
  getBackendHealthProbe,
  getBeautifulAiStatusProbe,
  recordBeautifulAiEditorOpened,
  type BeautifulAiPresentation,
  type BeautifulAiStatus,
  type BackendHealthProbe,
  type BeautifulAiStatusProbe
} from "@/lib/beautifulAi";
import { toFriendlyError } from "@/lib/errorMessage";
import { downloadEstimatePdf } from "@/lib/pdf";
import { downloadProposalPowerPoint, downloadSummaryProposalPowerPoint } from "@/lib/pptx";
import { canUseWorkFeatures, getRoleLabel, isAdminRole, isManagerCompatibleRole, type CreatableUserRole } from "@/lib/roles";
import { appendUsageLog, buildScopedStorageKey, readUsageLogs, type UsageLogEntry } from "@/lib/storage";
import { trackEvent } from "@/lib/analytics";
import type { AnalysisResponse, ProposalRequest } from "@/types/proposal";

import {
  MAX_ASSISTANT_QUESTIONS,
  aiEmployeeRoles,
  allInputText,
  applyChatAnswersToForm,
  budgetOptions,
  buildAiCoworkerReviews,
  buildAiMinutes,
  buildAiRecommendations,
  buildAutoFlowMessage,
  buildAutomationConcept,
  buildBossReport,
  buildBrowserUsePlan,
  buildChatAnswersFromExtracted,
  buildChatReadiness,
  buildCoachQuestions,
  buildCompanyResearch,
  buildDashboardMetrics,
  buildDisplayedWinProbability,
  buildDraftEmail,
  buildEasyMissingItems,
  buildErrorAdvice,
  buildExportMarkdown,
  buildFormFromExtracted,
  buildHearingResultSummary,
  buildHearingSheet,
  buildInfoChecks,
  buildInternalFaq,
  buildInternalMail,
  buildInternalMinutes,
  buildInternalReport,
  buildInternalSummary,
  buildInternalTasks,
  buildLiveProjectSummary,
  buildMcpConcept,
  buildMeetingEvaluation,
  buildMonthlyDashboardMetrics,
  buildNextMeetingPrep,
  buildOutputDigest,
  buildPreMeetingChecklist,
  buildPreviewSlides,
  buildProjectBriefFromEasyInput,
  buildProposalPlan,
  buildQualityScore,
  buildRealtimeQuestion,
  buildRoleGuidance,
  buildSalesDailyReport,
  buildSalesOpportunityScore,
  buildSimilarCases,
  buildStrategyCards,
  buildUrlInsight,
  buildWinRateCoachAdvice,
  buildWinRateImprovements,
  chatQuestionFlow,
  classifyKnowledge,
  cmsOptions,
  deadlineOptions,
  deriveCompetitorPoints,
  deriveDealEvaluation,
  deriveEstimateSummary,
  deriveSalesIndicators,
  deriveWinningStrategy,
  downloadTextFile,
  easySamples,
  extractClientName,
  extractProposalInfo,
  extractPurposeList,
  fillMissingExtractedInfo,
  fillMissingProposalForm,
  findNextMissingQuestionIndex,
  formatDateTime,
  formatEstimateRange,
  hashWorkspaceSeed,
  initialAgentSteps,
  initialChatMessages,
  initialEasyInput,
  initialMinimalInput,
  initialModeCounts,
  mcpConnectorCards,
  normalizeForm,
  operationGuideSteps,
  patchFormFromEasyInput,
  patchFormFromMinimalInput,
  purposeOptions,
  roleplayScenarios,
  safeHistoryParse,
  sanitizeFileName,
  sourceTemplates,
  starsFromPriority,
  workModeGroups,
  workModeMap,
  workModeTabs
} from "@/components/app-shell/logic";
export { wizardSteps, buildWizardMessage } from "@/components/app-shell/logic";

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
  const [isCreatingBeautifulAi, setIsCreatingBeautifulAi] = useState(false);
  const [beautifulAiStatus, setBeautifulAiStatus] = useState<BeautifulAiStatus | null>(null);
  const [beautifulAiStatusProbe, setBeautifulAiStatusProbe] = useState<BeautifulAiStatusProbe | null>(null);
  const [beautifulAiHealthProbe, setBeautifulAiHealthProbe] = useState<BackendHealthProbe | null>(null);
  const [beautifulAiResult, setBeautifulAiResult] = useState<BeautifulAiPresentation | null>(null);
  const [beautifulAiError, setBeautifulAiError] = useState("");
  const [error, setError] = useState("");
  const [lastDownloadRetry, setLastDownloadRetry] = useState<"pptx" | "summary-pptx" | "estimate-pdf" | "beautiful-ai" | null>(null);
  const [copyState, setCopyState] = useState<"idle" | "copied">("idle");
  const [healthSnapshot, setHealthSnapshot] = useState<HealthSnapshot | null>(null);
  const [usageLogs, setUsageLogs] = useState<UsageLogEntry[]>([]);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [workspaceContext, setWorkspaceContext] = useState<WorkspaceContext | null>(null);
  const [workspaceContextError, setWorkspaceContextError] = useState("");
  const [isWorkspaceContextLoading, setIsWorkspaceContextLoading] = useState(false);
  const [pilotStatus, setPilotStatus] = useState<PilotStatus | null>(null);
  const [showPilotChecklist, setShowPilotChecklist] = useState(false);
  const [managedUsers, setManagedUsers] = useState<ManagedUser[]>([]);
  const [crmCustomers, setCrmCustomers] = useState<CrmCustomer[]>([]);
  const [crmProjects, setCrmProjects] = useState<CrmProject[]>([]);
  const [dbLogCount, setDbLogCount] = useState(0);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [feedbackEntries, setFeedbackEntries] = useState<FeedbackEntry[]>([]);
  const [feedbackSummary, setFeedbackSummary] = useState<FeedbackSummary>(emptyFeedbackSummary);
  const [usageDashboard, setUsageDashboard] = useState<UsageDashboardData | null>(null);
  const [isDownloadingUsageCsv, setIsDownloadingUsageCsv] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState<FeedbackRating | "">("");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [pilotFeedbackScores, setPilotFeedbackScores] = useState<PilotFeedbackScores>(initialPilotFeedbackScores);
  const [feedbackStatus, setFeedbackStatus] = useState<"idle" | "sending" | "sent">("idle");
  const [feedbackError, setFeedbackError] = useState("");
  const [isGuideEnabled, setIsGuideEnabled] = useState(true);
  const [showGuideTutorial, setShowGuideTutorial] = useState(false);
  const [hasViewedOrganizedResult, setHasViewedOrganizedResult] = useState(false);
  const [autoFlowStatus, setAutoFlowStatus] = useState<AutoFlowStatus>("idle");
  const [isAutoGenerationPaused, setIsAutoGenerationPaused] = useState(false);
  const [hasDownloadedSummary, setHasDownloadedSummary] = useState(false);
  const [qualityGateUnlocked, setQualityGateUnlocked] = useState(false);
  const [beautifulAiQualityGate, setBeautifulAiQualityGate] = useState<QualityGateRecord | null>(null);
  const [beautifulAiQualityGateError, setBeautifulAiQualityGateError] = useState("");
  const [isBeautifulAiQualityGateLoading, setIsBeautifulAiQualityGateLoading] = useState(false);
  const [isAdminMenuOpen, setIsAdminMenuOpen] = useState(false);
  const [isUatMode, setIsUatMode] = useState(false);
  const [isSimpleDetailMode, setIsSimpleDetailMode] = useState(false);
  const autoAnalyzeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const autoReviewTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastAutoAnalyzedSourceRef = useRef("");
  const lastAutoGeneratedSignatureRef = useRef("");
  const loginAnalyticsTrackedRef = useRef(false);
  const pasteAnalyticsTrackedRef = useRef(false);

  useEffect(() => {
    setHistory(safeHistoryParse(window.localStorage.getItem(buildScopedStorageKey(HISTORY_KEY))));
    setUsageLogs(readUsageLogs());
    setShowGuideTutorial(window.localStorage.getItem(GUIDE_TUTORIAL_KEY) !== "true");
    void refreshAccountData();
    const handler = () => void refreshAccountData();
    window.addEventListener("ready-crew-auth-changed", handler);
    return () => window.removeEventListener("ready-crew-auth-changed", handler);
  }, []);

  useEffect(() => {
    if (rawSourceText.trim().length >= 10 && !pasteAnalyticsTrackedRef.current) {
      pasteAnalyticsTrackedRef.current = true;
      trackEvent({ name: "case_paste", feature: "proposal", status: "success", meta: { source: "paste" } });
    }
    if (!rawSourceText.trim()) {
      pasteAnalyticsTrackedRef.current = false;
    }
  }, [rawSourceText]);

  useEffect(() => {
    if (isUatMode && isManagerCompatibleRole(currentUser?.role)) {
      setIsAdminMenuOpen(true);
    }
    if (isUatMode && currentUser && !isManagerCompatibleRole(currentUser.role)) {
      setIsUatMode(false);
    }
    if (currentUser && !isManagerCompatibleRole(currentUser.role)) {
      setIsSimpleDetailMode(false);
    }
  }, [currentUser, currentUser?.role, isUatMode]);

  useEffect(() => {
    if (!result) {
      setQualityGateUnlocked(false);
      setBeautifulAiQualityGate(null);
      setBeautifulAiQualityGateError("");
      setBeautifulAiResult(null);
      setBeautifulAiError("");
    }
  }, [result]);

  async function refreshBeautifulAiVerification(hasUser = Boolean(getStoredUser())) {
    const [healthProbe, statusProbe] = await Promise.all([
      getBackendHealthProbe(),
      hasUser ? getBeautifulAiStatusProbe() : Promise.resolve<BeautifulAiStatusProbe | null>(null)
    ]);
    setBeautifulAiHealthProbe(healthProbe);
    setBeautifulAiStatusProbe(statusProbe);
    setBeautifulAiStatus(statusProbe?.status ?? null);
  }

  async function refreshWorkspaceContext() {
    setIsWorkspaceContextLoading(true);
    setWorkspaceContextError("");
    try {
      const context = await getWorkspaceContext();
      setWorkspaceContext(context);
    } catch {
      setWorkspaceContext(null);
      setWorkspaceContextError("Organization / Workspace情報を取得できません。ログイン状態とBackend接続を確認してください。");
    } finally {
      setIsWorkspaceContextLoading(false);
    }
  }

  function resetWorkspaceScopedState() {
    setResult(null);
    setEditablePreviewSlides([]);
    setCompanyResearch(null);
    setExtractedInfo(null);
    setUrlInsight(null);
    setHistory([]);
    setCrmCustomers([]);
    setCrmProjects([]);
    setAuditLogs([]);
    setFeedbackEntries([]);
    setFeedbackSummary(emptyFeedbackSummary);
    setUsageDashboard(null);
    setBeautifulAiResult(null);
    setBeautifulAiError("");
    setBeautifulAiQualityGate(null);
    setBeautifulAiQualityGateError("");
    setQualityGateUnlocked(false);
    setHasDownloadedSummary(false);
    setHasViewedOrganizedResult(false);
    setAutoFlowStatus("idle");
    setIsAutoGenerationPaused(false);
    setError("");
    setLastDownloadRetry(null);
  }

  async function handleWorkspaceSwitch(organizationId: number, workspaceId: number) {
    setIsWorkspaceContextLoading(true);
    setWorkspaceContextError("");
    try {
      const switched = await switchWorkspaceContext({ organization_id: organizationId, workspace_id: workspaceId });
      const storedUser = getStoredUser();
      if (storedUser) {
        saveAuthUser({
          ...storedUser,
          current_organization_id: switched.current.organization_id,
          current_workspace_id: switched.current.workspace_id
        });
      }
      resetWorkspaceScopedState();
      await refreshWorkspaceContext();
      await refreshAccountData();
    } catch {
      setWorkspaceContextError("このWorkspaceへ切り替える権限がありません。管理者に確認してください。");
    } finally {
      setIsWorkspaceContextLoading(false);
    }
  }

  async function refreshAccountData() {
    const storedUser = getStoredUser();
    setCurrentUser(storedUser);
    if (storedUser) {
      try {
        await refreshBeautifulAiVerification(true);
        await refreshWorkspaceContext();
      } catch {
        setBeautifulAiStatusProbe(null);
        setBeautifulAiHealthProbe(null);
        setBeautifulAiStatus(null);
      }
    } else {
      void refreshBeautifulAiVerification(false);
      setBeautifulAiStatusProbe(null);
      setBeautifulAiStatus(null);
      setWorkspaceContext(null);
      setWorkspaceContextError("");
    }
    let nextPilotStatus: PilotStatus | null = null;
    try {
      const status = await getPilotStatus();
      nextPilotStatus = status.pilot;
      setPilotStatus(status.pilot);
    } catch {
      setPilotStatus(null);
    }
    if (storedUser && nextPilotStatus?.pilot_mode && !isAdminRole(storedUser.role)) {
      const checklistKey = buildScopedStorageKey(`${PILOT_CHECKLIST_KEY}-${storedUser.id}`);
      setShowPilotChecklist(window.localStorage.getItem(checklistKey) === null);
    } else {
      setShowPilotChecklist(false);
    }
    if (storedUser && !loginAnalyticsTrackedRef.current) {
      loginAnalyticsTrackedRef.current = true;
      trackEvent({ name: "login", feature: "auth", status: "success", meta: { source: "app" } });
    }
    if (!storedUser) {
      loginAnalyticsTrackedRef.current = false;
      setDbLogCount(0);
      setManagedUsers([]);
      setAuditLogs([]);
      setFeedbackEntries([]);
      setFeedbackSummary(emptyFeedbackSummary);
      setUsageDashboard(null);
      return;
    }
    try {
      const crm = await getCrm();
      setCrmCustomers(crm.customers);
      setCrmProjects(crm.projects);
    } catch {
      setCrmCustomers([]);
      setCrmProjects([]);
    }
    if (!isAdminRole(storedUser.role)) {
      setDbLogCount(0);
      setManagedUsers([]);
      setAuditLogs([]);
      setFeedbackEntries([]);
      setFeedbackSummary(emptyFeedbackSummary);
      setUsageDashboard(null);
      return;
    }
    try {
      const logs = await getDbLogs();
      setDbLogCount(logs.logs.length);
    } catch {
      setDbLogCount(0);
    }
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
    try {
      const feedback = await getFeedback();
      setFeedbackEntries(feedback.feedback);
      setFeedbackSummary(feedback.summary);
    } catch {
      setFeedbackEntries([]);
    }
    try {
      const usage = await getUsageDashboard();
      setUsageDashboard(usage.dashboard);
    } catch {
      setUsageDashboard(null);
    }
  }

  const canSubmit = useMemo(() => {
    return form.project_brief.trim().length >= 20 && !isLoading;
  }, [form.project_brief, isLoading]);
  const currentWorkspaceId = useMemo(
    () => hashWorkspaceSeed(rawSourceText || form.project_brief || companyHomeUrl || "default"),
    [companyHomeUrl, form.project_brief, rawSourceText]
  );
  const isMaintenanceMode = Boolean(pilotStatus?.maintenance_mode);
  const canGenerate = canUseWorkFeatures(currentUser?.role) && !isMaintenanceMode;
  const canDownloadMainOutputs = Boolean(result && canGenerate && qualityGateUnlocked);
  const isBeautifulAiQualityGateForCurrentProject = beautifulAiQualityGate?.project_id === currentWorkspaceId;
  const isBeautifulAiQualityGateComplete = Boolean(
    isBeautifulAiQualityGateForCurrentProject &&
      (beautifulAiQualityGate?.completed || beautifulAiQualityGate?.bypassed || beautifulAiQualityGate?.download_unlocked)
  );
  const isBeautifulAiReady = Boolean(beautifulAiStatus?.enabled);
  const isBeautifulAiConfigured = Boolean(beautifulAiStatus?.configured);
  const isBeautifulAiMock = Boolean(beautifulAiStatus?.mock ?? beautifulAiHealthProbe?.beautifulAiMock);
  const isBeautifulAiStatusApiReachable = Boolean(beautifulAiStatusProbe?.apiReachable);
  const isBeautifulAiRouteFound = Boolean(
    (beautifulAiHealthProbe?.beautifulAiRouteRegistered ?? true) && (beautifulAiStatusProbe?.routeFound ?? false)
  );
  const isBeautifulAiAdmin = isAdminRole(currentUser?.role);
  const isBeautifulAiRoleAllowed = canUseWorkFeatures(currentUser?.role);
  const isBeautifulAiOutputBusy =
    isDownloadingPowerPoint ||
    isDownloadingSummaryPowerPoint ||
    isDownloadingEstimatePdf ||
    isCreatingBeautifulAi;
  const beautifulAiUnavailableMessage =
    beautifulAiStatusProbe?.message ||
    beautifulAiStatus?.message ||
    "Beautiful.ai status APIを確認中です。";
  const beautifulAiDiagnosticRows = useMemo(
    () => [
      {
        label: "Proposal Ready",
        value: result ? "true" : "false",
        pass: Boolean(result),
        required: true,
        note: result ? "提案書作成済み" : "先に提案書を作成してください。"
      },
      {
        label: "Quality Gate",
        value: isBeautifulAiQualityGateComplete ? "true" : "false",
        pass: isBeautifulAiQualityGateComplete,
        required: true,
        note: isBeautifulAiQualityGateComplete
          ? beautifulAiQualityGate?.bypassed
            ? "Backend Quality Gateは管理者バイパス済みです。"
            : "Backend Quality Gateは完了済みです。"
          : isBeautifulAiQualityGateLoading
            ? "Backend Quality Gateを確認中です。"
            : beautifulAiQualityGateError || "AI Workspaceの提出前確認ゲートを完了してください。"
      },
      {
        label: "Admin",
        value: isBeautifulAiAdmin ? "true" : "false",
        pass: isBeautifulAiAdmin,
        required: false,
        note: "管理者と一般利用者が作成できます。"
      },
      {
        label: "Role Allowed",
        value: isBeautifulAiRoleAllowed ? "true" : "false",
        pass: isBeautifulAiRoleAllowed,
        required: true,
        note: currentUser?.role ? `現在の権限: ${getRoleLabel(currentUser.role)}` : "ログイン状態を確認してください。"
      },
      {
        label: "Status API",
        value: isBeautifulAiStatusApiReachable ? "true" : "false",
        pass: isBeautifulAiStatusApiReachable,
        required: true,
        note: beautifulAiStatusProbe?.httpStatus ? `HTTP ${beautifulAiStatusProbe.httpStatus}` : "未確認"
      },
      {
        label: "Route Found",
        value: isBeautifulAiRouteFound ? "true" : "false",
        pass: isBeautifulAiRouteFound,
        required: true,
        note: isBeautifulAiRouteFound ? "/api/beautiful-ai/status を確認済み" : "RenderのBeautiful.ai router登録を確認してください。"
      },
      {
        label: "Enabled",
        value: isBeautifulAiReady ? "true" : "false",
        pass: isBeautifulAiReady,
        required: true,
        note: beautifulAiStatus?.message || beautifulAiUnavailableMessage
      },
      {
        label: "Configured",
        value: isBeautifulAiConfigured ? "true" : "false",
        pass: isBeautifulAiConfigured,
        required: true,
        note: isBeautifulAiConfigured ? "Backend側の設定あり" : "RenderのBEAUTIFUL_AI_API_KEYまたはMOCK設定を確認してください。"
      },
      {
        label: "Mock",
        value: isBeautifulAiMock ? "true" : "false",
        pass: true,
        required: false,
        note: isBeautifulAiMock ? "モックモードです。" : "実APIモードです。"
      },
      {
        label: "API Mode",
        value: beautifulAiStatus?.api_mode || beautifulAiHealthProbe?.beautifulAiApiMode || "unknown",
        pass: true,
        required: false,
        note: (beautifulAiStatus?.api_mode || beautifulAiHealthProbe?.beautifulAiApiMode) === "structured" ? "Structured APIを使用します。" : "Prompt APIを使用します。"
      },
      {
        label: "Maintenance",
        value: isMaintenanceMode ? "true" : "false",
        pass: !isMaintenanceMode,
        required: true,
        note: isMaintenanceMode ? "Maintenance Mode中は新規作成を停止します。" : "通常稼働中"
      },
      {
        label: "Other Output Busy",
        value: isBeautifulAiOutputBusy ? "true" : "false",
        pass: !isBeautifulAiOutputBusy,
        required: true,
        note: isBeautifulAiOutputBusy ? "他の出力処理が完了するまで待ってください。" : "出力処理待ちはありません。"
      }
    ],
    [
      beautifulAiStatus?.message,
      beautifulAiStatus?.api_mode,
      beautifulAiHealthProbe?.beautifulAiApiMode,
      beautifulAiStatusProbe?.httpStatus,
      beautifulAiUnavailableMessage,
      beautifulAiQualityGate?.bypassed,
      beautifulAiQualityGateError,
      currentUser?.role,
      isBeautifulAiQualityGateComplete,
      isBeautifulAiQualityGateLoading,
      isBeautifulAiAdmin,
      isBeautifulAiConfigured,
      isBeautifulAiMock,
      isBeautifulAiOutputBusy,
      isBeautifulAiReady,
      isBeautifulAiRoleAllowed,
      isBeautifulAiRouteFound,
      isBeautifulAiStatusApiReachable,
      isMaintenanceMode,
      result
    ]
  );
  const beautifulAiBlockingReasons = useMemo(
    () => beautifulAiDiagnosticRows.filter((row) => row.required && !row.pass),
    [beautifulAiDiagnosticRows]
  );
  const canCreateBeautifulAiOutput = beautifulAiBlockingReasons.length === 0;
  const beautifulAiDisabledReason =
    beautifulAiBlockingReasons.length > 0
      ? `Beautiful.aiボタンが無効です: ${beautifulAiBlockingReasons.map((row) => row.label).join("、")}`
      : "Beautiful.aiで提案書を作成できます。";
  const beautifulAiPreparedPayload = useMemo(
    () =>
      result
        ? buildBeautifulAiPayload(currentWorkspaceId, result.powerpoint_generation_data, form, result.analysis.win_probability)
        : null,
    [currentWorkspaceId, form, result]
  );
  const handleQualityGateChange = useCallback((unlocked: boolean, gate?: QualityGateRecord | null) => {
    setQualityGateUnlocked(unlocked);
    if (gate !== undefined) {
      setBeautifulAiQualityGate(gate);
      setBeautifulAiQualityGateError("");
    }
  }, []);
  const refreshBeautifulAiQualityGate = useCallback(async () => {
    if (!result || !currentUser) {
      setQualityGateUnlocked(false);
      setBeautifulAiQualityGate(null);
      setBeautifulAiQualityGateError("");
      return;
    }

    setIsBeautifulAiQualityGateLoading(true);
    setBeautifulAiQualityGateError("");
    try {
      const response = await getQualityGate(currentWorkspaceId);
      const gate = response.gate ?? null;
      const unlocked = Boolean(
        gate?.project_id === currentWorkspaceId && (gate.completed || gate.bypassed || gate.download_unlocked)
      );
      setBeautifulAiQualityGate(gate);
      setQualityGateUnlocked(unlocked);
    } catch {
      setBeautifulAiQualityGate(null);
      setQualityGateUnlocked(false);
      setBeautifulAiQualityGateError("Backend Quality Gateを取得できません。ログイン状態とBackend接続を確認してください。");
    } finally {
      setIsBeautifulAiQualityGateLoading(false);
    }
  }, [currentUser, currentWorkspaceId, result]);
  useEffect(() => {
    void refreshBeautifulAiQualityGate();
  }, [refreshBeautifulAiQualityGate]);

  async function generateFromGuidedFlow() {
    if (!rawSourceText.trim() && !companyHomeUrl.trim() && !form.project_brief.trim()) {
      setError("案件情報を入力してください。案件メール、議事録、ヒアリングメモをそのまま貼り付けられます。");
      return;
    }
    const baseExtracted = extractProposalInfo(rawSourceText || form.project_brief, companyHomeUrl);
    const nextExtracted = fillMissingExtractedInfo(baseExtracted, companyHomeUrl);
    const nextInsight = buildUrlInsight(companyHomeUrl, rawSourceText || form.project_brief, nextExtracted);
    const nextForm = fillMissingProposalForm(buildFormFromExtracted(form, nextExtracted, nextInsight));

    setExtractedInfo(nextExtracted);
    setUrlInsight(nextInsight);
    setHasViewedOrganizedResult(true);
    setChatAnswers(buildChatAnswersFromExtracted(baseExtracted));
    setChatQuestionIndex(chatQuestionFlow.length);
    setAssistantQuestionCount(MAX_ASSISTANT_QUESTIONS);
    setAutoFlowStatus("generating");
    setError("");
    await generateProposal(nextForm);
  }

  async function completeGuidedQualityGate(checklistItems: string[]) {
    if (!canUseWorkFeatures(currentUser?.role)) {
      setError("このアカウントでは提出前チェックを完了できません。管理者へ権限確認を依頼してください。");
      return;
    }
    try {
      setError("");
      const response = await completeQualityGate(currentWorkspaceId, checklistItems);
      handleQualityGateChange(Boolean(response.gate?.download_unlocked), response.gate ?? null);
      await refreshBeautifulAiQualityGate();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}。${friendly.action}`);
    }
  }

  const hasGuideInput = Boolean(rawSourceText.trim() || companyHomeUrl.trim() || form.project_brief.trim());
  const hasGuideOrganizedContent = Boolean(extractedInfo || urlInsight || form.project_brief.trim().length >= 20);
  const currentGuideStep: GuideStep = result
    ? 5
    : !hasGuideInput
      ? 1
      : !hasGuideOrganizedContent
        ? 2
        : !hasViewedOrganizedResult
          ? 3
          : 4;
  const wizardChatQuestion = chatQuestionFlow[Math.min(chatQuestionIndex, chatQuestionFlow.length - 1)];
  const autoFlowMessage = useMemo(
    () => buildAutoFlowMessage(autoFlowStatus, result, wizardChatQuestion),
    [autoFlowStatus, result, wizardChatQuestion]
  );
  const activeProgressKey = useMemo(() => {
    if (isDownloadingSummaryPowerPoint || result) return "download";
    if (autoFlowStatus === "generating") return "writing";
    if (autoFlowStatus === "question" || autoFlowStatus === "reviewing" || autoFlowStatus === "analyzing") return "checking";
    if (autoFlowStatus === "typing") return "reading";
    return "idle";
  }, [autoFlowStatus, isDownloadingSummaryPowerPoint, result]);

  const easyMissingItems = useMemo(() => buildEasyMissingItems(easyInput), [easyInput]);
  const canOrganizeEasyInput = easyMissingItems.length === 0;
  const chatReadiness = useMemo(() => buildChatReadiness(chatAnswers), [chatAnswers]);
  const infoChecks = useMemo(() => buildInfoChecks(form), [form]);
  const missingItems = useMemo(() => infoChecks.filter((item) => !item.found), [infoChecks]);
  const liveProjectSummary = useMemo(() => buildLiveProjectSummary(form, missingItems), [form, missingItems]);
  const proposalReviewItems = useMemo(() => {
    const sourceText = allInputText(form);
    const purposes = extractPurposeList(sourceText);
    const inferredValues = ["未定", "要確認", "競合未確認", "提案先企業", "Webサイト制作・改善", "問い合わせ改善・信頼感向上"];
    const formatValue = (value: string, fallback: string) => ({
      value: value.trim() || fallback,
      inferred: !value.trim() || inferredValues.some((item) => value.trim() === item || fallback === item)
    });
    return [
      { label: "会社名", ...formatValue(extractClientName(form), "提案先企業") },
      { label: "案件内容", ...formatValue(extractedInfo?.projectContent || form.project_brief.slice(0, 80), "Webサイト制作・改善") },
      { label: "目的", ...formatValue(purposes.join("、"), "問い合わせ改善・信頼感向上") },
      { label: "予算", ...formatValue(form.budget_range, "未定") },
      { label: "納期", ...formatValue(form.desired_launch_timing, "要確認") },
      { label: "CMS", ...formatValue(form.cms_required, "要確認") },
      { label: "不足情報", value: missingItems.length ? missingItems.map((item) => item.label).slice(0, 4).join("、") : "大きな不足なし", inferred: false }
    ];
  }, [extractedInfo?.projectContent, form, missingItems]);
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

  function showMaintenanceError() {
    setError("現在メンテナンス中です。履歴確認やCRM閲覧はできますが、新規作成・PPT/PDF作成は一時停止しています。");
  }
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
    { label: "今日の作成数", value: `${total}件`, note: "この画面で作成したAI出力" },
      { label: "営業提案数", value: `${modeUsageCounts.sales}件`, note: "提案書・PPT・見積につながる出力" },
      { label: "議事録作成数", value: `${modeUsageCounts.minutes}件`, note: "会議メモから整理" },
      { label: "メール作成数", value: `${modeUsageCounts.mail}件`, note: "件名・本文・返信案" },
      { label: "タスク整理数", value: `${modeUsageCounts.tasks}件`, note: "依頼や議事録から分解" },
      { label: "AI削減時間", value: `${savedMinutes}分`, note: "1件45分削減として概算" },
      { label: "使えそう", value: `${feedbackSummary.usable}件`, note: "提案書フィードバック" },
      { label: "修正すれば使えそう", value: `${feedbackSummary.needs_revision}件`, note: "提案書フィードバック" },
      { label: "使いにくい", value: `${feedbackSummary.hard_to_use}件`, note: "提案書フィードバック" },
      { label: "コメント", value: `${feedbackSummary.comments}件`, note: "フィードバックコメント" }
    ];
  }, [feedbackSummary, modeUsageCounts]);
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
    trackEvent({
      name: "feature_used",
      feature: outputType || featureName,
      status,
      errorType,
      meta: {
        output: outputType,
        category: errorType || undefined
      }
    });
    setUsageLogs(readUsageLogs());
  }

  function openDetailsPanel(panelId: string) {
    const panel = document.getElementById(panelId) as HTMLElement | null;
    if (panel) {
      let parentDetails = panel.parentElement?.closest("details") as HTMLDetailsElement | null;
      while (parentDetails) {
        parentDetails.open = true;
        parentDetails = parentDetails.parentElement?.closest("details") as HTMLDetailsElement | null;
      }
      if (panel instanceof HTMLDetailsElement) {
        panel.open = true;
      }
      panel.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    if (panelId.startsWith("admin-") && panelId !== "admin-menu-panel") {
      const adminMenu = document.getElementById("admin-menu-panel") as HTMLDetailsElement | null;
      if (adminMenu) {
        adminMenu.open = true;
        setIsAdminMenuOpen(true);
        window.setTimeout(() => openDetailsPanel(panelId), 0);
        return;
      }
    }
    const globalMenu = document.getElementById("global-detail-menu") as HTMLDetailsElement | null;
    if (globalMenu) {
      globalMenu.open = true;
    }
    globalMenu?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function openOrganizedResultPanel() {
    setHasViewedOrganizedResult(true);
    openDetailsPanel("result-sales-panel");
  }

  async function handleCreateUser(payload: { email: string; password: string; role: CreatableUserRole }) {
    await createUser(payload);
    const users = await listUsers();
    setManagedUsers(users.users);
  }

  async function handleToggleUser(userId: number, isActive: boolean) {
    await updateUserActive(userId, isActive);
    const users = await listUsers();
    setManagedUsers(users.users);
  }

  async function handleTogglePilot(userId: number, pilotEnabled: boolean) {
    await updateUserPilot(userId, { pilot_enabled: pilotEnabled });
    const users = await listUsers();
    setManagedUsers(users.users);
    await refreshAccountData();
  }

  async function handleConfirmPilotChecklist() {
    if (!currentUser) return;
    setError("");
    try {
      await confirmPilotChecklist();
      window.localStorage.setItem(buildScopedStorageKey(`${PILOT_CHECKLIST_KEY}-${currentUser.id}`), "true");
      setShowPilotChecklist(false);
      await refreshAccountData();
    } catch (caught) {
      setError(toFriendlyError(caught).title);
    }
  }

  async function handleDownloadUsageCsv() {
    setIsDownloadingUsageCsv(true);
    setError("");
    try {
      const blob = await downloadUsageDashboardCsv();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `AI営業秘書_利用状況_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}。${friendly.action}`);
    } finally {
      setIsDownloadingUsageCsv(false);
    }
  }

  function openOperationsTarget(target: string) {
    if (target === "new-case") {
      document.querySelector(".wizard-main-input textarea, .one-screen-input textarea")?.scrollIntoView({ behavior: "smooth", block: "center" });
      const input = document.querySelector(".wizard-main-input textarea, .one-screen-input textarea") as HTMLTextAreaElement | null;
      input?.focus();
      return;
    }
    if (target === "operations-search") {
      const input = document.querySelector(".operations-search-panel input") as HTMLInputElement | null;
      input?.scrollIntoView({ behavior: "smooth", block: "center" });
      input?.focus();
      return;
    }
    openDetailsPanel(target);
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
    recordUsage("AI社員", allInputText(form).length + rawSourceText.length, "agent-workflow", "success");
    setRecentFeatures((current) => ["AI社員", ...current.filter((item) => item !== "AI社員")].slice(0, 5));
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
        : "必要な情報が揃いました。提案書を作成できます。";

    setExtractedInfo(nextExtracted);
    setUrlInsight(nextInsight);
    setHasViewedOrganizedResult(false);
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
        text: nextMissingIndex >= 0 ? missingQuestion : "このまま「今の内容で作成する」から提案書を作成できます。"
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
    setHasViewedOrganizedResult(false);
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
          text: "追加情報として反映しました。必要であれば、この内容で提案書を作成できます。"
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
        ? `${nextReadiness.ready ? "提案書を作成できます。精度を上げるため、未確認の項目だけ確認します。\n" : ""}${chatQuestionFlow[nextIndex].label}だけ教えてください。\n${chatQuestionFlow[nextIndex].question}`
        : "必要な情報が揃いました。提案書を作成できます。まだ未確認の項目があっても「今の内容で作成する」から進められます。";

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
      setError("まずはチャットで案件内容を1つ入力してください。途中でも作成できます。");
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
      window.localStorage.setItem(buildScopedStorageKey(HISTORY_KEY), JSON.stringify(nextHistory));
    } catch {
      setError("作成は完了しましたが、履歴のローカル保存に失敗しました。ブラウザの保存容量を確認してください。");
    }
  }

  function saveHistory(response: AnalysisResponse, sourceForm = form) {
    const entry: HistoryEntry = {
      id: `${Date.now()}`,
      createdAt: new Date().toISOString(),
      title: response.powerpoint_generation_data.deck_title || "提案書初稿",
      clientName: extractClientName(sourceForm, response),
      form: sourceForm,
      result: response
    };
    const nextHistory = [entry, ...history.filter((item) => item.id !== entry.id)].slice(0, MAX_HISTORY_COUNT);
    persistHistory(nextHistory);
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isMaintenanceMode) {
      showMaintenanceError();
      return;
    }
    if (!canGenerate) {
      setError("閲覧のみの一般利用者では提案書を作成できません。管理者へ権限変更を依頼してください。");
      return;
    }
    if (!canSubmit) {
      return;
    }
    setForm((current) => fillMissingProposalForm(current));
    setError("");
    setIsConfirmOpen(true);
  }

  async function generateProposal(sourceForm = form) {
    if (isMaintenanceMode) {
      showMaintenanceError();
      return;
    }
    if (!canGenerate) {
      setError("閲覧のみの一般利用者では提案書を作成できません。管理者へ権限変更を依頼してください。");
      return;
    }
    const nextForm = fillMissingProposalForm(sourceForm);
    setForm(nextForm);
    setIsConfirmOpen(false);
    setIsLoading(true);
    setAutoFlowStatus("generating");
    setError("");
    setCopyState("idle");
    const analysisStartedAt = performance.now();
    trackEvent({ name: "ai_analysis_start", feature: "proposal", status: "start", meta: { mode: inputMode } });

    try {
      const response = await analyzeProposal(nextForm);
      const durationMs = performance.now() - analysisStartedAt;
      trackEvent({ name: "ai_analysis_complete", feature: "proposal", status: "success", durationMs, meta: { mode: inputMode } });
      trackEvent({ name: "proposal_generated", feature: "proposal", status: "success", durationMs, meta: { output: "markdown" } });
      setResult(response);
      setBeautifulAiResult(null);
      setBeautifulAiError("");
      setHasDownloadedSummary(false);
      setFeedbackRating("");
      setFeedbackComment("");
      setPilotFeedbackScores(initialPilotFeedbackScores);
      setFeedbackStatus("idle");
      setFeedbackError("");
      setAutoFlowStatus("complete");
      saveHistory(response, nextForm);
      recordModeUsage("sales");
      recordUsage("提案書作成", allInputText(nextForm).length, "markdown", "success");
      void refreshAccountData();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      trackEvent({
        name: "ai_analysis_complete",
        feature: "proposal",
        status: "failure",
        durationMs: performance.now() - analysisStartedAt,
        errorType: friendly.category,
        meta: { category: friendly.category }
      });
      recordUsage("提案書作成", allInputText(nextForm).length, "markdown", "failure", friendly.category);
      setError(`${friendly.title}。${friendly.action}`);
      setAutoFlowStatus("idle");
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
    if (isMaintenanceMode) {
      showMaintenanceError();
      return;
    }
    if (!canGenerate) {
      setError("閲覧のみの一般利用者ではPowerPointを作成できません。管理者へ権限変更を依頼してください。");
      return;
    }
    if (targetResult === result && !qualityGateUnlocked) {
      setError("提出前確認ゲートを完了すると、PowerPointをダウンロードできます。AI Workspaceの確認項目をチェックしてください。");
      return;
    }
    if (summary) {
      setIsDownloadingSummaryPowerPoint(true);
    } else {
      setIsDownloadingPowerPoint(true);
    }
    setError("");
    const downloadStartedAt = performance.now();
    const downloadEventName = summary ? "summary_ppt_download" : "detail_ppt_download";
    const downloadFeatureName = summary ? "summary_ppt" : "detail_ppt";

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
      trackEvent({
        name: downloadEventName,
        feature: downloadFeatureName,
        status: "success",
        durationMs: performance.now() - downloadStartedAt,
        meta: { output: summary ? "summary-pptx" : "pptx" }
      });
      recordUsage(summary ? "要約PowerPoint" : "PowerPoint", allInputText(targetForm).length, summary ? "summary-pptx" : "pptx", "success");
      if (summary) {
        setHasDownloadedSummary(true);
      }
      setLastDownloadRetry(null);
      void refreshAccountData();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      trackEvent({
        name: downloadEventName,
        feature: downloadFeatureName,
        status: "failure",
        durationMs: performance.now() - downloadStartedAt,
        errorType: friendly.category,
        meta: { category: friendly.category }
      });
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
    if (isMaintenanceMode) {
      showMaintenanceError();
      return;
    }
    if (!canGenerate) {
      setError("閲覧のみの一般利用者では見積書PDFを作成できません。管理者へ権限変更を依頼してください。");
      return;
    }
    if (targetResult === result && !qualityGateUnlocked) {
      setError("提出前確認ゲートを完了すると、見積PDFをダウンロードできます。AI Workspaceの確認項目をチェックしてください。");
      return;
    }
    setIsDownloadingEstimatePdf(true);
    setError("");
    const pdfStartedAt = performance.now();

    try {
      await downloadEstimatePdf(
        targetResult.powerpoint_generation_data,
        targetForm,
        targetResult.analysis.win_probability
      );
      trackEvent({
        name: "estimate_pdf_download",
        feature: "estimate_pdf",
        status: "success",
        durationMs: performance.now() - pdfStartedAt,
        meta: { output: "estimate-pdf" }
      });
      recordUsage("見積書PDF", allInputText(targetForm).length, "estimate-pdf", "success");
      setLastDownloadRetry(null);
      void refreshAccountData();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      trackEvent({
        name: "estimate_pdf_download",
        feature: "estimate_pdf",
        status: "failure",
        durationMs: performance.now() - pdfStartedAt,
        errorType: friendly.category,
        meta: { category: friendly.category }
      });
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

  async function createBeautifulAiCurrent() {
    if (isMaintenanceMode) {
      showMaintenanceError();
      return;
    }
    if (!result) {
      setBeautifulAiError("先に提案書を作成してください。");
      setError("先に提案書を作成してください。");
      return;
    }
    if (!canCreateBeautifulAiOutput) {
      const message = beautifulAiBlockingReasons[0]?.note || beautifulAiDisabledReason;
      setBeautifulAiError(message);
      setError(message);
      return;
    }

    setIsCreatingBeautifulAi(true);
    setBeautifulAiError("");
    setError("");
    const startedAt = performance.now();
    try {
      if (!beautifulAiPreparedPayload) {
        throw new Error("Beautiful.ai送信データを作成できませんでした。");
      }
      const response = await createBeautifulAiPresentation(beautifulAiPreparedPayload);
      setBeautifulAiResult(response);
      trackEvent({
        name: "beautiful_ai_created",
        feature: "beautiful_ai",
        status: "success",
        durationMs: performance.now() - startedAt,
        meta: { output: "beautiful-ai" }
      });
      recordUsage("Beautiful.ai", allInputText(form).length, "beautiful-ai", "success");
      setLastDownloadRetry(null);
      void refreshAccountData();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      const message = `${friendly.title}。${friendly.action} 既存PPTXも利用できます。`;
      setBeautifulAiError(message);
      setError(message);
      setLastDownloadRetry("beautiful-ai");
      trackEvent({
        name: "beautiful_ai_created",
        feature: "beautiful_ai",
        status: "failure",
        durationMs: performance.now() - startedAt,
        errorType: friendly.category,
        meta: { category: friendly.category }
      });
      recordUsage("Beautiful.ai", allInputText(form).length, "beautiful-ai", "failure", friendly.category);
    } finally {
      setIsCreatingBeautifulAi(false);
    }
  }

  function openBeautifulAiUrl(url: string) {
    if (!url || !beautifulAiResult?.presentation_id) return;
    void recordBeautifulAiEditorOpened(beautifulAiResult.presentation_id).catch(() => undefined);
    window.open(url, "_blank", "noopener,noreferrer");
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
    if (lastDownloadRetry === "beautiful-ai") {
      await createBeautifulAiCurrent();
      return;
    }
    await downloadEstimatePdfFor(result, form);
  }

  function rerunAiWorkspaceAgent(agent: AiWorkspaceAgentKey) {
    if (agent === "secretary") {
      if (!rawSourceText.trim() && !companyHomeUrl.trim()) {
        setError("案件メール、議事録、URLを貼り付けるとAI秘書が情報整理を再実行できます。");
        return;
      }
      setResult(null);
      setError("");
      setIsAutoGenerationPaused(false);
      lastAutoAnalyzedSourceRef.current = "";
      lastAutoGeneratedSignatureRef.current = "";
      setAutoFlowStatus("analyzing");
      window.setTimeout(() => applySourceExtraction(false), 80);
      return;
    }

    if (agent === "sales") {
      const nextForm = fillMissingProposalForm(form);
      if (nextForm.project_brief.trim().length < 20) {
        setError("AI営業を再実行するには、案件メールまたは案件概要を入力してください。");
        return;
      }
      void generateProposal(nextForm);
      return;
    }

    if (agent === "director") {
      setError("");
      setHasViewedOrganizedResult(true);
      setAutoFlowStatus(result ? "complete" : "reviewing");
      openDetailsPanel("result-sales-panel");
      return;
    }

    if (agent === "pm") {
      setError("");
      setHasViewedOrganizedResult(true);
      openDetailsPanel("result-sales-panel");
      return;
    }

    setError("");
    setAutoFlowStatus(result ? "complete" : "reviewing");
    if (result) {
      openDetailsPanel("result-sales-panel");
    }
  }

  async function sendProposalFeedback() {
    if (!feedbackRating) {
      setFeedbackError("評価を1つ選んでください。");
      return;
    }
    const pilotScoresText = pilotFeedbackQuestions
      .map((question) => `${question.label}: ${pilotFeedbackScores[question.key] || "未回答"}/5`)
      .join("\n");
    const sanitizedComment = [pilotScoresText, feedbackComment.trim()]
      .filter(Boolean)
      .join("\n\nコメント:\n")
      .slice(0, 1000);
    setFeedbackStatus("sending");
    setFeedbackError("");
    try {
      const response = await submitFeedback({
        rating: feedbackRating,
        comment: sanitizedComment,
        feature_name: "提案書作成"
      });
      setFeedbackSummary(response.summary);
      setFeedbackEntries((current) => [response.feedback, ...current.filter((item) => item.id !== response.feedback.id)]);
      setFeedbackStatus("sent");
    } catch {
      setFeedbackStatus("idle");
      setFeedbackError("フィードバック送信に失敗しました。時間を置いて再度お試しください。");
    }
  }

  function restoreHistory(entry: HistoryEntry) {
    setForm(normalizeForm(entry.form));
    setInputMode("detail");
    setChatMessages([
      ...initialChatMessages,
      {
        id: `assistant-history-${Date.now()}`,
        role: "assistant",
        text: "作成履歴を読み込みました。右側の整理済み概要を確認し、必要に応じて提案書を再ダウンロードできます。"
      }
    ]);
    setChatAnswers({});
    setChatQuestionIndex(0);
    setAssistantQuestionCount(0);
    setChatDraft("");
    setResult(entry.result);
    setError("");
    setCopyState("idle");
    setFeedbackRating("");
    setFeedbackComment("");
    setPilotFeedbackScores(initialPilotFeedbackScores);
    setFeedbackStatus("idle");
    setFeedbackError("");
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
        text: "サンプル案件を読み込みました。右側の整理済み概要を確認し、そのまま提案書を作成できます。"
      }
    ]);
    setHasViewedOrganizedResult(false);
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
    setHasViewedOrganizedResult(false);
    recordUsage("サンプル体験", buildProjectBriefFromEasyInput(sample).length, "sample", "success");
  }

  function startSampleExperience() {
    fillSample("renewal");
    setRawSourceText(sampleBrief);
    setResult(null);
    setError("");
    setCopyState("idle");
    setHasDownloadedSummary(false);
    setIsAutoGenerationPaused(false);
    setHasViewedOrganizedResult(false);
    setAssistantQuestionCount(MAX_ASSISTANT_QUESTIONS);
    setChatQuestionIndex(chatQuestionFlow.length);
    setChatDraft("");
    lastAutoAnalyzedSourceRef.current = "";
    lastAutoGeneratedSignatureRef.current = "";
    setAutoFlowStatus("typing");
    setChatMessages([
      ...initialChatMessages,
      {
        id: `assistant-sample-experience-${Date.now()}`,
        role: "assistant",
        text: "サンプルを入れました。内容を確認し、AIが自動で整理します。"
      }
    ]);
    window.localStorage.setItem(GUIDE_TUTORIAL_KEY, "true");
    setShowGuideTutorial(false);
  }

  useEffect(() => {
    const source = rawSourceText.trim();
    if (!source) {
      setAutoFlowStatus("idle");
      lastAutoAnalyzedSourceRef.current = "";
      lastAutoGeneratedSignatureRef.current = "";
      return;
    }
    if (result || isLoading || source.length < 8) {
      return;
    }
    if (isAutoGenerationPaused) {
      return;
    }
    if (lastAutoAnalyzedSourceRef.current === source) {
      return;
    }

    setAutoFlowStatus("typing");
    if (autoAnalyzeTimerRef.current) {
      clearTimeout(autoAnalyzeTimerRef.current);
    }

    autoAnalyzeTimerRef.current = setTimeout(() => {
      lastAutoAnalyzedSourceRef.current = source;
      setAutoFlowStatus("analyzing");
      const ok = applySourceExtraction(false);
      if (ok) {
        window.setTimeout(() => setAutoFlowStatus("question"), 350);
      }
    }, 1000);

    return () => {
      if (autoAnalyzeTimerRef.current) {
        clearTimeout(autoAnalyzeTimerRef.current);
      }
    };
  }, [isAutoGenerationPaused, isLoading, rawSourceText, result]);

  useEffect(() => {
    if (!rawSourceText.trim() || result || isLoading) {
      return;
    }
    if (autoFlowStatus !== "question") {
      return;
    }
    if (isAutoGenerationPaused) {
      return;
    }
    if (chatQuestionIndex < chatQuestionFlow.length && assistantQuestionCount < MAX_ASSISTANT_QUESTIONS) {
      return;
    }

    const nextForm = fillMissingProposalForm(form);
    if (nextForm.project_brief.trim().length < 20) {
      return;
    }

    const signature = `${nextForm.project_brief}|${nextForm.client_company_info}|${nextForm.budget_range}|${nextForm.desired_launch_timing}`;
    if (lastAutoGeneratedSignatureRef.current === signature) {
      return;
    }
    lastAutoGeneratedSignatureRef.current = signature;
    setAutoFlowStatus("reviewing");
  }, [assistantQuestionCount, autoFlowStatus, chatQuestionIndex, form, isAutoGenerationPaused, isLoading, rawSourceText, result]);

  useEffect(() => {
    if (autoFlowStatus !== "reviewing" || isAutoGenerationPaused || result || isLoading) {
      return;
    }

    if (autoReviewTimerRef.current) {
      clearTimeout(autoReviewTimerRef.current);
    }

    autoReviewTimerRef.current = setTimeout(() => {
      void generateProposal(fillMissingProposalForm(form));
    }, 3200);

    return () => {
      if (autoReviewTimerRef.current) {
        clearTimeout(autoReviewTimerRef.current);
      }
    };
  }, [autoFlowStatus, form, isAutoGenerationPaused, isLoading, result]);

  const renderBeautifulAiDiagnosticsPanel = (variant: "primary" | "detail" = "primary") => (
    <section
      className="beautiful-ai-diagnostics"
      aria-label="Beautiful.aiボタンの利用条件"
      data-testid={variant === "primary" ? "beautiful-ai-disabled-reasons" : "beautiful-ai-disabled-reasons-detail"}
    >
      <div className="beautiful-ai-diagnostics-heading">
        <strong>Beautiful.ai利用条件</strong>
        <span className={canCreateBeautifulAiOutput ? "is-ready" : "is-blocked"}>
          {canCreateBeautifulAiOutput ? "作成できます" : "現在は無効です"}
        </span>
      </div>
      <div className="beautiful-ai-check-grid">
        {beautifulAiDiagnosticRows.map((row) => (
          <article
            className={row.pass ? "is-ok" : row.required ? "is-alert" : "is-neutral"}
            key={row.label}
          >
            <div>
              <span>{row.label}</span>
              <strong>{row.value}</strong>
            </div>
            <small>{row.note}</small>
          </article>
        ))}
      </div>
      <p className={canCreateBeautifulAiOutput ? "beautiful-ai-status-message" : "beautiful-ai-version-warning"}>
        {beautifulAiDisabledReason}
      </p>
    </section>
  );

  const canSeeSimpleDetailMode = Boolean(currentUser && isManagerCompatibleRole(currentUser.role));
  const isGuidedDetailMode = Boolean(canSeeSimpleDetailMode && isSimpleDetailMode);
  const roleDisplayLabel = currentUser?.role ? getRoleLabel(currentUser.role) : "未ログイン";
  const guidedGenerationStages: GuidedProgressStage[] = useMemo(() => {
    const hasResult = Boolean(result);
    const hasError = Boolean(error && !isLoading && !hasResult);
    const running = isLoading || ["typing", "analyzing", "question", "reviewing", "generating"].includes(autoFlowStatus);
    return [
      {
        label: "案件整理",
        status: hasResult ? "done" : running ? "done" : hasError ? "error" : "waiting",
        helper: "貼り付け内容から会社名・課題・目的を整理します"
      },
      {
        label: "提案作成",
        status: hasResult ? "done" : isLoading || autoFlowStatus === "generating" ? "running" : hasError ? "error" : "waiting",
        helper: "提案ストーリーと見積概要を作成します"
      },
      {
        label: "品質確認",
        status: hasResult ? "done" : isLoading ? "running" : "waiting",
        helper: "不足やAI推測項目を確認します"
      },
      {
        label: "スケジュール確認",
        status: hasResult ? "done" : isLoading ? "running" : "waiting",
        helper: "納期と進行の前提を整理します"
      },
      {
        label: "最終確認",
        status: hasResult ? "done" : isLoading ? "running" : "waiting",
        helper: "出力前の確認内容をまとめます"
      }
    ];
  }, [autoFlowStatus, error, isLoading, result]);
  const guidedSummaryItems: GuidedSummaryItem[] = useMemo(
    () => [
      { label: "案件概要", value: form.project_brief || extractedInfo?.projectContent || rawSourceText, inferred: !form.project_brief && Boolean(rawSourceText) },
      { label: "課題", value: extractedInfo?.trouble || form.client_company_info || "要確認", inferred: !extractedInfo?.trouble },
      { label: "提案方針", value: result?.analysis?.proposal_policy || "提案書作成後に表示されます" },
      { label: "スケジュール", value: form.desired_launch_timing || extractedInfo?.deadline || "要確認", inferred: !form.desired_launch_timing },
      { label: "見積概要", value: form.budget_range || extractedInfo?.budget || "未定", inferred: !form.budget_range },
      { label: "注意事項", value: result?.analysis?.quality_check?.human_review_notes || "AI作成内容は提出前に人が確認してください" },
      { label: "AI推測項目", value: [!form.budget_range ? "予算" : "", !form.desired_launch_timing ? "納期" : "", !form.cms_required ? "CMS" : ""].filter(Boolean).join("、") || "大きな推測項目はありません", inferred: true }
    ],
    [extractedInfo?.budget, extractedInfo?.deadline, extractedInfo?.projectContent, extractedInfo?.trouble, form.budget_range, form.client_company_info, form.cms_required, form.desired_launch_timing, form.project_brief, rawSourceText, result?.analysis?.proposal_policy, result?.analysis?.quality_check?.human_review_notes]
  );
  const beautifulAiSimpleRequirements: BeautifulAiSimpleRequirement[] = useMemo(
    () => [
      { label: "提案書を作成する", passed: Boolean(result), reason: "先に提案書を作成してください" },
      { label: "提出前チェックを完了する", passed: isBeautifulAiQualityGateComplete, reason: "提出前チェックが完了していません" },
      {
        label: "Beautiful.aiを有効にする",
        passed: isBeautifulAiReady && isBeautifulAiConfigured && isBeautifulAiStatusApiReachable && isBeautifulAiRouteFound,
        reason: "Beautiful.aiの設定が完了していません"
      },
      { label: "メンテナンス中ではない", passed: !isMaintenanceMode, reason: "現在メンテナンス中です" },
      { label: "作成権限がある", passed: isBeautifulAiRoleAllowed, reason: "このアカウントには作成権限がありません" },
      { label: "他の出力処理が終わっている", passed: !isBeautifulAiOutputBusy, reason: "他の出力処理を実行中です" }
    ],
    [isBeautifulAiConfigured, isBeautifulAiOutputBusy, isBeautifulAiQualityGateComplete, isBeautifulAiReady, isBeautifulAiRoleAllowed, isBeautifulAiRouteFound, isBeautifulAiStatusApiReachable, isMaintenanceMode, result]
  );
  const beautifulAiSimpleDisabledReason =
    beautifulAiSimpleRequirements.find((item) => !item.passed)?.reason || "Beautiful.aiでプレゼンを作成できます";
  const guidedWorkspacePanel = (
    <WorkspaceProgress
      status={autoFlowStatus}
      hasInput={hasGuideInput}
      hasResult={Boolean(result)}
      isLoading={isLoading}
      canAdminRerun={isAdminRole(currentUser?.role)}
      canPersist={isManagerCompatibleRole(currentUser?.role) || canUseWorkFeatures(currentUser?.role)}
      canRequestReview={canUseWorkFeatures(currentUser?.role)}
      canCompleteQualityGate={canUseWorkFeatures(currentUser?.role)}
      canBypassQualityGate={isAdminRole(currentUser?.role)}
      onQualityGateChange={handleQualityGateChange}
      onRerunAgent={rerunAiWorkspaceAgent}
      workspaceSeed={[
        currentUser?.id ?? "anonymous",
        workspaceContext?.current?.organization_id ?? "org-default",
        workspaceContext?.current?.workspace_id ?? "workspace-default",
        rawSourceText || form.project_brief || companyHomeUrl || "default"
      ].join("::")}
      workspaceTitle={result?.powerpoint_generation_data.deck_title || form.client_company_info || form.project_brief.slice(0, 60) || "AI Workspace提案"}
    />
  );
  const guidedPresentationReviewPanel = (
    <PresentationReviewPanel
      projectId={currentWorkspaceId}
      projectName={result?.powerpoint_generation_data.deck_title || form.client_company_info || "AI Workspace提案"}
      powerpointData={result?.powerpoint_generation_data ?? null}
      beautifulAiPresentationId={beautifulAiResult?.presentation_id}
      beautifulAiPayload={beautifulAiPreparedPayload}
      currentRole={currentUser?.role}
    />
  );
  const guidedProposalOptimizationPanel = (
    <ProposalOptimizationPanel
      projectId={currentWorkspaceId}
      currentRole={currentUser?.role}
      enabled={Boolean(result)}
    />
  );

  const handleLogout = useCallback(() => {
    void logoutCurrentSession().finally(() => {
      window.dispatchEvent(new Event("ready-crew-auth-changed"));
      window.location.reload();
    });
  }, []);

  return (
    <AuthGate>
    <main className={`app-shell ${isDarkMode ? "dark-mode" : ""} ${isGuidedDetailMode ? "guided-detail-mode" : "guided-normal-mode"}`}>
      <Header isDarkMode={isDarkMode} onToggleDarkMode={() => setIsDarkMode((current) => !current)} onLogout={handleLogout} />
      {currentUser && (
        <WorkspaceSwitcher
          context={workspaceContext}
          isLoading={isWorkspaceContextLoading}
          error={workspaceContextError}
          onSwitch={handleWorkspaceSwitch}
          onRefresh={() => void refreshWorkspaceContext()}
        />
      )}
      {pilotStatus?.pilot_mode && (
        <section className="pilot-mode-banner" aria-label="社内試験利用中">
          <strong>社内試験利用中</strong>
          <span>AI作成内容は社外提出前に必ず人が確認してください。</span>
          {pilotStatus.pilot_end_date && <small>終了予定: {pilotStatus.pilot_end_date}</small>}
        </section>
      )}
      {isMaintenanceMode && (
        <section className="maintenance-banner" role="alert">
          <strong>メンテナンス中</strong>
          <span>新規作成・PPT/PDF作成は一時停止しています。履歴確認、CRM、管理画面は利用できます。</span>
        </section>
      )}
      {currentUser && isGuidedDetailMode && <ReleaseUpdatesPanel />}
      {currentUser && isGuidedDetailMode && (
        <BeautifulAiStatusCard
          statusProbe={beautifulAiStatusProbe}
          healthProbe={beautifulAiHealthProbe}
          onRefresh={() => void refreshBeautifulAiVerification(true)}
          canViewDiagnostics={isManagerCompatibleRole(currentUser.role)}
        />
      )}
      {currentUser && isManagerCompatibleRole(currentUser.role) && isGuidedDetailMode && (
        <UatModePanel
          enabled={isUatMode}
          onToggle={() => setIsUatMode((current) => !current)}
          currentUser={currentUser}
          workspaceContext={workspaceContext}
          healthSnapshot={healthSnapshot}
          beautifulAiStatusProbe={beautifulAiStatusProbe}
          beautifulAiHealthProbe={beautifulAiHealthProbe}
          maintenanceMode={isMaintenanceMode}
          canEditResults={isAdminRole(currentUser.role)}
          onOpenAdminMenu={() => setIsAdminMenuOpen(true)}
          onJump={openOperationsTarget}
        />
      )}

      {currentUser && (
        <GuidedFlow
          beautifulAiCanCreate={canCreateBeautifulAiOutput}
          beautifulAiDisabledReason={beautifulAiSimpleDisabledReason}
          beautifulAiError={beautifulAiError}
          beautifulAiIsCreating={isCreatingBeautifulAi}
          beautifulAiRequirements={beautifulAiSimpleRequirements}
          beautifulAiResult={beautifulAiResult}
          canCompleteQualityGate={canUseWorkFeatures(currentUser.role)}
          canDownloadMainOutputs={canDownloadMainOutputs}
          canGenerate={canGenerate}
          canSeeDetailMode={canSeeSimpleDetailMode}
          detailMode={isGuidedDetailMode}
          errorMessage={error}
          generationStages={guidedGenerationStages}
          hasDownloadedSummary={hasDownloadedSummary}
          hasProposal={Boolean(result)}
          isDownloadingDetail={isDownloadingPowerPoint}
          isDownloadingPdf={isDownloadingEstimatePdf}
          isDownloadingSummary={isDownloadingSummaryPowerPoint}
          isGenerating={isLoading}
          onCompleteQualityGate={(items) => completeGuidedQualityGate(items)}
          onCreateBeautifulAi={() => createBeautifulAiCurrent()}
          onDownloadDetail={() => downloadPowerPoint()}
          onDownloadPdf={() => downloadEstimatePdfCurrent()}
          onDownloadSummary={() => downloadSummaryPowerPoint()}
          onGenerate={() => generateFromGuidedFlow()}
          onNewCase={resetChat}
          onOpenBeautifulAiUrl={openBeautifulAiUrl}
          onOpenCrm={() => openDetailsPanel("dashboard-panel")}
          onRetry={lastDownloadRetry ? () => void retryLastDownload() : undefined}
          onShowGuide={() => setShowGuideTutorial(true)}
          onSourceTextChange={(value) => {
            setRawSourceText(value);
            setHasViewedOrganizedResult(false);
            if (result) setResult(null);
          }}
          onToggleDetailMode={() => setIsSimpleDetailMode((current) => !current)}
          onUseSample={startSampleExperience}
          organizationName={workspaceContext?.current?.organization_name || "Ready Crew"}
          panels={{
            workspaceProgress: guidedWorkspacePanel,
            presentationReview: guidedPresentationReviewPanel,
            proposalOptimization: guidedProposalOptimizationPanel,
            beautifulAiDiagnostics: renderBeautifulAiDiagnosticsPanel("detail")
          }}
          qualityGate={beautifulAiQualityGate}
          qualityGateComplete={isBeautifulAiQualityGateComplete}
          qualityGateIsLoading={isBeautifulAiQualityGateLoading}
          roleLabel={roleDisplayLabel}
          showSalesCopilotMarker
          sourceText={rawSourceText}
          summaryItems={guidedSummaryItems}
          workspaceName={workspaceContext?.current?.workspace_name || "営業部"}
        />
      )}

      {currentUser && isGuidedDetailMode && (
        <RealOperationsDashboard
          projects={crmProjects}
          history={history}
          usageLogs={usageLogs}
          auditLogs={auditLogs}
          usageDashboard={usageDashboard}
          feedbackSummary={feedbackSummary}
          qualityGateWaiting={Boolean(result && !qualityGateUnlocked)}
          hasProposalResult={Boolean(result)}
          isAdmin={isAdminRole(currentUser.role)}
          onOpenPanel={openOperationsTarget}
          onFocusNewCase={() => openOperationsTarget("new-case")}
        />
      )}

      <section className="ai-wizard-shell legacy-guided-detail" aria-label="詳細作業パネル">
        <WorkspaceProgress
          status={autoFlowStatus}
          hasInput={hasGuideInput}
          hasResult={Boolean(result)}
          isLoading={isLoading}
          canAdminRerun={isAdminRole(currentUser?.role)}
          canPersist={isManagerCompatibleRole(currentUser?.role) || canUseWorkFeatures(currentUser?.role)}
          canRequestReview={canUseWorkFeatures(currentUser?.role)}
          canCompleteQualityGate={canUseWorkFeatures(currentUser?.role)}
          canBypassQualityGate={isAdminRole(currentUser?.role)}
          onQualityGateChange={handleQualityGateChange}
          onRerunAgent={rerunAiWorkspaceAgent}
          workspaceSeed={[
            currentUser?.id ?? "anonymous",
            workspaceContext?.current?.organization_id ?? "org-default",
            workspaceContext?.current?.workspace_id ?? "workspace-default",
            rawSourceText || form.project_brief || companyHomeUrl || "default"
          ].join("::")}
          workspaceTitle={result?.powerpoint_generation_data.deck_title || form.client_company_info || form.project_brief.slice(0, 60) || "AI Workspace提案"}
        />
        <PresentationReviewPanel
          projectId={currentWorkspaceId}
          projectName={result?.powerpoint_generation_data.deck_title || form.client_company_info || "AI Workspace提案"}
          powerpointData={result?.powerpoint_generation_data ?? null}
          beautifulAiPresentationId={beautifulAiResult?.presentation_id}
          beautifulAiPayload={beautifulAiPreparedPayload}
          currentRole={currentUser?.role}
        />
        <ProposalOptimizationPanel
          projectId={currentWorkspaceId}
          currentRole={currentUser?.role}
          enabled={Boolean(result)}
        />

        <div className="wizard-chat-card" aria-live="polite">
          <div className="wizard-avatar">AI</div>
          <div className="wizard-chat-bubble">
            <span>AI営業秘書</span>
            <p>{autoFlowMessage}</p>
          </div>
        </div>

        <div className="wizard-progress-flow" aria-label="進行状況">
          <div className={`wizard-ai-character is-${activeProgressKey}`}>
            <span className="ai-character-head">AI</span>
            <span className="ai-character-shadow" />
          </div>
          {[
            { key: "reading", label: "案件を読み取り中" },
            { key: "checking", label: "不足情報を確認中" },
            { key: "writing", label: "提案書を作成中" },
            { key: "download", label: "ダウンロード準備中" }
          ].map((stage) => (
            <div className={activeProgressKey === stage.key ? "is-active" : ""} key={stage.key}>
              <span />
              <strong>{stage.label}</strong>
            </div>
          ))}
        </div>

        <article className="wizard-current-card wizard-chat-workspace">
          {errorAdvice && (
            <div className="wizard-recovery-card" role="alert">
              <strong>{errorAdvice.title}</strong>
              <p>{errorAdvice.action}</p>
            </div>
          )}

          {!result && (
            <>
              <div className="wizard-input-lead">
                <strong>案件メールを貼ってください</strong>
                <p>Ready Crewの案件メール、議事録、ヒアリングメモをそのまま貼り付けてください。</p>
              </div>
              <label className="field wizard-main-input wizard-paste-only">
                <span>案件メール・URL・議事録・メモ</span>
                <textarea
                  value={rawSourceText}
                  onChange={(event) => {
                    setRawSourceText(event.target.value);
                    setHasViewedOrganizedResult(false);
                    setResult(null);
                    setIsAutoGenerationPaused(false);
                    setAutoFlowStatus(event.target.value.trim() ? "typing" : "idle");
                  }}
                  placeholder="Ready Crewの案件メール、議事録、ヒアリングメモをそのまま貼り付けてください。URLだけでも大丈夫です。"
                  rows={10}
                />
              </label>

              <div className="wizard-sample-experience">
                <button className="primary-button" type="button" onClick={startSampleExperience}>
                  <Sparkles size={18} aria-hidden="true" />
                  まずはサンプルで体験
                </button>
                <button className="secondary-button" type="button" onClick={() => setShowGuideTutorial(true)}>
                  使い方を見る
                </button>
                <span>サンプル案件で、要約PPTダウンロードまでの流れを確認できます。</span>
              </div>

              {autoFlowStatus !== "idle" && (
                <div className={`wizard-auto-status is-${autoFlowStatus}`} aria-live="polite">
                  {(autoFlowStatus === "analyzing" || autoFlowStatus === "generating") && <Loader2 className="spin" size={16} aria-hidden="true" />}
                  <strong>今AIがやっていること</strong>
                  <span>{autoFlowMessage}</span>
                </div>
              )}

              <p className="wizard-short-notice">AI作成内容は提出前に必ず人が確認してください。</p>

              {autoFlowStatus === "reviewing" && (
                <div className="wizard-review-card" aria-label="作成前確認">
                  <div>
                    <strong>作成前の確認</strong>
                    <p>問題なければ自動で提案書を作成します。</p>
                  </div>
                  <dl>
                    {proposalReviewItems.map((item) => (
                      <div key={item.label}>
                        <dt>{item.label}</dt>
                        <dd>
                          {item.value}
                          {item.inferred && <span>AI推測</span>}
                        </dd>
                      </div>
                    ))}
                  </dl>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => {
                      setIsAutoGenerationPaused(true);
                      setAutoFlowStatus("typing");
                      lastAutoAnalyzedSourceRef.current = "";
                      if (autoReviewTimerRef.current) {
                        clearTimeout(autoReviewTimerRef.current);
                      }
                    }}
                  >
                    修正する
                  </button>
                </div>
              )}

              {autoFlowStatus === "question" && chatQuestionIndex < chatQuestionFlow.length && (
                <form className="wizard-question-form" onSubmit={submitChatAnswer}>
                  <label className="field">
                    <span>{wizardChatQuestion.label}だけ教えてください。</span>
                    <input
                      value={chatDraft}
                      onChange={(event) => setChatDraft(event.target.value)}
                      placeholder={wizardChatQuestion.placeholder}
                    />
                    <small>Enterで反映します</small>
                  </label>
                </form>
              )}

              {chatMessages.length > initialChatMessages.length && (
                <div className="wizard-chat-feed" aria-label="AIの整理結果">
                  {chatMessages.slice(-3).map((message) => (
                    <div className={`wizard-feed-message is-${message.role}`} key={message.id}>
                      <span>{message.role === "assistant" ? "AI" : "あなた"}</span>
                      <p>{message.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {result && (
            <div className="wizard-action-panel">
              <div className="wizard-primary-actions">
                <button
                  className="ppt-download-button summary wizard-main-action"
                  type="button"
                  onClick={downloadSummaryPowerPoint}
                  disabled={!canDownloadMainOutputs || isDownloadingPowerPoint || isDownloadingSummaryPowerPoint || isDownloadingEstimatePdf || isCreatingBeautifulAi}
                >
                  {isDownloadingSummaryPowerPoint ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <FileDown size={18} aria-hidden="true" />}
                  <span><strong>要約PPTをダウンロード</strong><small>発表用</small></span>
                </button>
                <button
                  className="ppt-download-button beautiful-ai"
                  type="button"
                  onClick={createBeautifulAiCurrent}
                  disabled={!canCreateBeautifulAiOutput}
                >
                  {isCreatingBeautifulAi ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Sparkles size={18} aria-hidden="true" />}
                  <span>
                    <strong>
                      {isCreatingBeautifulAi
                        ? "Beautiful.aiでスライドをデザインしています"
                        : isBeautifulAiReady
                          ? "Beautiful.aiで提案書を作成"
                          : "Beautiful.aiは未設定"}
                    </strong>
                    <small>外部デザイン編集用</small>
                  </span>
                </button>
                {renderBeautifulAiDiagnosticsPanel()}
                {beautifulAiResult && (
                  <div className="beautiful-ai-result" aria-live="polite">
                    <strong>Beautiful.ai提案書を作成しました</strong>
                    <div>
                      {beautifulAiResult.editor_url && (
                        <button className="text-button" type="button" onClick={() => openBeautifulAiUrl(beautifulAiResult.editor_url)}>
                          Beautiful.aiで編集
                        </button>
                      )}
                      {beautifulAiResult.player_url && (
                        <button className="text-button" type="button" onClick={() => openBeautifulAiUrl(beautifulAiResult.player_url)}>
                          プレゼンテーションを表示
                        </button>
                      )}
                    </div>
                    <small>共有権限はBeautiful.ai側で確認してください。</small>
                  </div>
                )}
                {beautifulAiError && <p className="beautiful-ai-error">{beautifulAiError}</p>}
                <details className="wizard-other-format-menu">
                  <summary>その他の出力</summary>
                  <div className="wizard-download-grid">
                    <button
                      className="ppt-download-button"
                      type="button"
                      onClick={downloadPowerPoint}
                      disabled={!canDownloadMainOutputs || isDownloadingPowerPoint || isDownloadingSummaryPowerPoint || isDownloadingEstimatePdf || isCreatingBeautifulAi}
                    >
                      {isDownloadingPowerPoint ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <FileDown size={18} aria-hidden="true" />}
                      <span><strong>通常PPT</strong><small>詳細提案用</small></span>
                    </button>
                    <button
                      className="ppt-download-button pdf"
                      type="button"
                      onClick={downloadEstimatePdfCurrent}
                      disabled={!canDownloadMainOutputs || isDownloadingPowerPoint || isDownloadingSummaryPowerPoint || isDownloadingEstimatePdf || isCreatingBeautifulAi}
                    >
                      {isDownloadingEstimatePdf ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <FileDown size={18} aria-hidden="true" />}
                      <span><strong>見積PDF</strong><small>見積確認用</small></span>
                    </button>
                    <button className="ppt-download-button markdown" type="button" onClick={() => downloadMarkdown()}>
                      <Download size={18} aria-hidden="true" />
                      <span><strong>原稿データ</strong><small>Markdown形式</small></span>
                    </button>
                  </div>
                  <div className="wizard-detail-groups">
                    {isAdminRole(currentUser?.role) && (
                      <section>
                        <strong>管理</strong>
                        <button type="button" onClick={() => openDetailsPanel("admin-menu-panel")}>ユーザー管理・監査ログ・設定</button>
                      </section>
                    )}
                    <section>
                      <strong>分析</strong>
                      <button type="button" onClick={openOrganizedResultPanel}>受注予測・品質スコア</button>
                      <button type="button" onClick={() => openDetailsPanel("company-research-panel")}>会社調査</button>
                    </section>
                    <section>
                      <strong>業務AI</strong>
                      <button type="button" onClick={() => openDetailsPanel("ai-functions-panel")}>議事録・メール・タスク・日報</button>
                    </section>
                    <section>
                      <strong>連携予定</strong>
                      <button type="button" onClick={() => openDetailsPanel("future-integration-panel")}>MCP・自動確認</button>
                    </section>
                    <section>
                      <strong>履歴</strong>
                      <button type="button" onClick={() => openDetailsPanel("dashboard-panel")}>作成履歴・CRM</button>
                    </section>
                  </div>
                </details>
              </div>
              <p className="wizard-short-notice">AI作成内容は提出前に必ず人が確認してください。</p>
            </div>
          )}

          {result && (
            <div className="wizard-check-panel">
              <strong>提出前チェックリスト</strong>
              <ul>
                <li>会社名に誤りがないか</li>
                <li>見積金額は妥当か</li>
                <li>納期は現実的か</li>
                <li>AI推測ラベルが付いた項目を確認したか</li>
                <li>社外提出前に上長確認したか</li>
              </ul>
            </div>
          )}

          {result && (
            <section className="proposal-feedback-panel" aria-label="提案書フィードバック">
              <div>
                <strong>この提案書は使えそうですか？</strong>
                <p>案件本文や顧客情報は保存しません。評価とコメントだけを社内改善に使います。</p>
              </div>
              <div className="feedback-rating-row">
                {(Object.keys(feedbackRatingLabels) as FeedbackRating[]).map((rating) => (
                  <label className={feedbackRating === rating ? "is-selected" : ""} key={rating}>
                    <input
                      checked={feedbackRating === rating}
                      disabled={feedbackStatus === "sent" || feedbackStatus === "sending"}
                      name="proposal-feedback-rating"
                      onChange={() => setFeedbackRating(rating)}
                      type="radio"
                    />
                    <span>{feedbackRatingLabels[rating]}</span>
                  </label>
                ))}
              </div>
              <div className="pilot-feedback-likert" aria-label="Pilot 5段階評価">
                <strong>Pilot評価（5段階）</strong>
                <p>コメント欄に顧客本文や案件本文を貼らないでください。</p>
                {pilotFeedbackQuestions.map((question) => (
                  <label key={question.key}>
                    <span>{question.label}</span>
                    <select
                      disabled={feedbackStatus === "sent" || feedbackStatus === "sending"}
                      value={pilotFeedbackScores[question.key]}
                      onChange={(event) =>
                        setPilotFeedbackScores((current) => ({
                          ...current,
                          [question.key]: Number(event.target.value)
                        }))
                      }
                    >
                      <option value={0}>未回答</option>
                      <option value={1}>1</option>
                      <option value={2}>2</option>
                      <option value={3}>3</option>
                      <option value={4}>4</option>
                      <option value={5}>5</option>
                    </select>
                  </label>
                ))}
              </div>
              <label className="field feedback-comment-field">
                <span>コメント</span>
                <textarea
                  disabled={feedbackStatus === "sent" || feedbackStatus === "sending"}
                  onChange={(event) => setFeedbackComment(event.target.value)}
                  placeholder="どこが良かったですか？ どこが分かりにくかったですか？"
                  rows={3}
                  value={feedbackComment}
                />
              </label>
              {feedbackError && <p className="feedback-error">{feedbackError}</p>}
              {feedbackStatus === "sent" ? (
                <p className="feedback-thanks">フィードバックを送信しました。ありがとうございます。</p>
              ) : (
                <button className="secondary-button" disabled={feedbackStatus === "sending"} onClick={() => void sendProposalFeedback()} type="button">
                  {feedbackStatus === "sending" ? "送信中" : "フィードバックを送信"}
                </button>
              )}
            </section>
          )}

          {result && hasDownloadedSummary && (
            <div className="wizard-next-action-panel">
              <strong>次にやること</strong>
              <ol>
                <li>社内確認する</li>
                <li>顧客へ送る前に修正する</li>
                <li>商談前チェックリストを見る</li>
              </ol>
            </div>
          )}
        </article>

        <details className="wizard-effect-foldout">
          <summary>このツールの効果</summary>
          <div className="wizard-effect-grid">
            <article>
              <strong>提案書作成時間を短縮</strong>
              <p>案件メールから叩き台を作成し、資料準備の初動を軽くします。</p>
            </article>
            <article>
              <strong>ヒアリング漏れを防止</strong>
              <p>予算、納期、CMS、競合などの不足情報を次回確認事項として整理します。</p>
            </article>
            <article>
              <strong>提案品質を標準化</strong>
              <p>課題、方針、見積、確認事項を同じ型でまとめ、属人化を抑えます。</p>
            </article>
            <article>
              <strong>商談準備を効率化</strong>
              <p>提出前チェックと次アクションを表示し、社内確認までつなげます。</p>
            </article>
          </div>
        </details>
      </section>

      <details className="advanced-foldout secondary-guidance-panel">
        <summary>入力ガイド・詳細操作を開く</summary>
      <section className="one-screen-start" aria-label="入力ガイド・詳細操作">
        <div className="one-screen-copy">
          <p className="eyebrow">はじめに</p>
          <h2>案件メールを貼るだけで、提案書・見積・商談準備をAIが整理します。</h2>
        </div>
        <div className="operation-guide-header">
          <div className="operation-guide-steps" aria-label="操作ステップガイド">
            {operationGuideSteps.map((item) => (
              <div className={currentGuideStep === item.step && isGuideEnabled ? "is-active" : ""} key={item.step}>
                <span>STEP {item.step}</span>
                <strong>{item.title}</strong>
              </div>
            ))}
          </div>
          <button className="guide-toggle-button" type="button" onClick={() => setIsGuideEnabled((current) => !current)}>
            操作ガイド{isGuideEnabled ? "ON" : "OFF"}
          </button>
        </div>
        <label className={`field one-screen-input ${isGuideEnabled && currentGuideStep === 1 ? "guide-target" : ""}`}>
          {isGuideEnabled && currentGuideStep === 1 && <span className="guide-label">まずここに貼り付け</span>}
          <span>案件メール・議事録・URLをここに貼り付け</span>
          <textarea
            value={rawSourceText}
            onChange={(event) => {
              setRawSourceText(event.target.value);
              setHasViewedOrganizedResult(false);
            }}
            placeholder="Ready Crew案件メール、商談メモ、Slack相談文、会社URLなどをそのまま貼り付けてください。"
            rows={8}
          />
        </label>
        <div className="one-screen-actions">
          <button className={`primary-button ${isGuideEnabled && currentGuideStep === 2 ? "guide-target" : ""}`} type="button" onClick={oneClickAutoGenerate} disabled={!canGenerate || isLoading}>
            {isGuideEnabled && currentGuideStep === 2 && <span className="guide-label button-guide-label">次に押す</span>}
            <Sparkles size={18} aria-hidden="true" />
            AIに全部おまかせ
          </button>
          <button className="secondary-button" type="button" onClick={autoPrepareProposal} disabled={!canGenerate || isLoading}>
            内容を整理
          </button>
          <button
            className={`secondary-button ${isGuideEnabled && currentGuideStep === 4 ? "guide-target" : ""}`}
            type="button"
            onClick={() => {
              if (canSubmit) {
                setIsConfirmOpen(true);
              } else {
                oneClickAutoGenerate();
              }
            }}
            disabled={!canGenerate || isLoading}
          >
            {isGuideEnabled && currentGuideStep === 4 && <span className="guide-label button-guide-label">次に押す</span>}
            提案書を作成
          </button>
        </div>
        <div className="one-screen-links">
          <button className="text-button" type="button" onClick={() => fillSample("renewal")}>サンプルを入れる</button>
          <button
            className="text-button"
            type="button"
            onClick={() => {
              setInputMode("easy");
              const panel = document.getElementById("detailed-sales-panel") as HTMLDetailsElement | null;
              if (panel) panel.open = true;
              panel?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            最小入力に切り替え
          </button>
          <button
            className="text-button"
            type="button"
            onClick={() => {
              const panel = document.getElementById("detailed-sales-panel") as HTMLDetailsElement | null;
              if (panel) panel.open = true;
              panel?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            詳細機能を開く
          </button>
          <button
            className={`text-button ${isGuideEnabled && (currentGuideStep === 3 || currentGuideStep === 5) ? "guide-target link-guide-target" : ""}`}
            type="button"
            onClick={() => {
              const panel = document.getElementById("result-sales-panel") as HTMLDetailsElement | null;
              if (panel) panel.open = true;
              setHasViewedOrganizedResult(true);
              panel?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            {isGuideEnabled && currentGuideStep === 3 && <span className="guide-label link-guide-label">次はこちら</span>}
            {isGuideEnabled && currentGuideStep === 5 && <span className="guide-label link-guide-label">次はこちら</span>}
            整理結果を見る
          </button>
        </div>
      </section>
      </details>

      <details className="advanced-foldout" id="dashboard-panel">
        <summary>ダッシュボードを見る</summary>
        <Dashboard
          dashboardMetrics={dashboardMetrics}
          monthlyDashboardMetrics={monthlyDashboardMetrics}
          operationDashboardMetrics={operationDashboardMetrics}
        />
        <CrmPanel customers={crmCustomers} projects={crmProjects} currentRole={currentUser?.role} onChanged={() => void refreshAccountData()} />
      </details>

      <WorkModeSection
        activeMode={activeMode}
        canGenerate={canGenerate}
        canShowExternalIntakeCandidates={!isAdminRole(currentUser?.role)}
        canSubmit={canSubmit}
        currentRole={currentUser?.role}
        recentFeatures={recentFeatures}
        setActiveMode={setActiveMode}
        setIsConfirmOpen={setIsConfirmOpen}
        workModeGroups={workModeGroups}
        workModeMap={workModeMap}
      />
      {isAdminRole(currentUser?.role) && (
        <AdminSection
          auditLogs={auditLogs}
          currentUser={currentUser}
          dbLogCount={dbLogCount}
          feedbackEntries={feedbackEntries}
          feedbackSummary={feedbackSummary}
          handleCreateUser={handleCreateUser}
          handleDownloadUsageCsv={handleDownloadUsageCsv}
          handleTogglePilot={handleTogglePilot}
          handleToggleUser={handleToggleUser}
          healthSnapshot={healthSnapshot}
          isAdminMenuOpen={isAdminMenuOpen}
          isDownloadingUsageCsv={isDownloadingUsageCsv}
          managedUsers={managedUsers}
          setHealthSnapshot={setHealthSnapshot}
          setIsAdminMenuOpen={setIsAdminMenuOpen}
          usageDashboard={usageDashboard}
          usageLogs={usageLogs}
        />
      )}

      {isManagerCompatibleRole(currentUser?.role) && (
        <details className="advanced-foldout release-menu-foldout" id="release-management-panel">
          <summary>リリース管理を開く</summary>
          <AdminReleaseManagementPanel />
        </details>
      )}

      {isManagerCompatibleRole(currentUser?.role) && (
        <details className="advanced-foldout review-menu-foldout" id="review-menu-panel">
          <summary>レビュー依頼一覧を開く</summary>
          <AdminReviewPanel />
        </details>
      )}

      <DigitalCoworkerSection
        agentSteps={agentSteps}
        aiCoworkerReviews={aiCoworkerReviews}
        aiEmployeeGuidance={aiEmployeeGuidance}
        aiEmployeeRoles={aiEmployeeRoles}
        automationSettings={automationSettings}
        companyHomeUrl={companyHomeUrl}
        companyResearch={companyResearch}
        isAgentRunning={isAgentRunning}
        mcpConnectorCards={mcpConnectorCards}
        runCompanyResearch={runCompanyResearch}
        runDigitalCoworkerAgent={runDigitalCoworkerAgent}
        selectedAiEmployee={selectedAiEmployee}
        setCompanyHomeUrl={setCompanyHomeUrl}
        setSelectedAiEmployee={setSelectedAiEmployee}
        toggleAutomation={toggleAutomation}
      />

      {activeMode === "sales" && (
        <>
      <SalesInfoSection />

      <details className="advanced-foldout" id="detailed-sales-panel">
        <summary>詳細入力・抽出結果を開く</summary>
      <section className="extractor-panel" id="case-input-panel" aria-label="AI情報抽出モード">
        <div className="extractor-heading">
          <div>
            <p className="eyebrow">AI情報整理</p>
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
            <strong>AIに全部おまかせ</strong>
            <p>貼り付け情報やURLから自動整理し、作成前確認まで進めます。</p>
          </div>
          <button className="primary-button auto-generate-button" type="button" onClick={oneClickAutoGenerate}>
            <Sparkles size={18} aria-hidden="true" />
            AIに全部おまかせ
          </button>
          <button className="secondary-button auto-generate-button" type="button" onClick={autoPrepareProposal}>
            <Bot size={18} aria-hidden="true" />
            内容を整理
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
          <div><span>4</span><strong>提案書作成</strong></div>
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
              内容を整理
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
      </details>

        </>
      )}

      {activeMode === "coach" && (
      <section className="meeting-coach-panel" aria-label="AI商談コーチ">
        <div className="coach-heading">
          <div>
            <p className="eyebrow">AI商談コーチ</p>
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
              <p className="eyebrow">議事録AI</p>
              <h2>議事録AI</h2>
              <p>会議メモ、文字起こし、チャットログから、決定事項・未決事項・ToDoを整理します。</p>
            </div>
            <button className="primary-button" type="button" onClick={generateMinutesMode}>
              <FileText size={18} aria-hidden="true" />
              議事録を作成
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
                <p className="empty-state">会議メモを入力して「議事録を作成」を押してください。未入力の場合は営業提案AIの商談メモから作成します。</p>
              )}
            </article>
          </div>
        </section>
      )}

      {activeMode === "mail" && (
        <section className="business-mode-panel" aria-label="メール作成AI">
          <div className="business-mode-heading">
            <div>
              <p className="eyebrow">メール作成AI</p>
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
              <p className="eyebrow">タスク整理AI</p>
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
              <p className="eyebrow">資料要約AI</p>
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
              <p className="eyebrow">日報・週報AI</p>
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
      <details className="advanced-foldout result-foldout" id="result-sales-panel" onToggle={(event) => {
        if ((event.currentTarget as HTMLDetailsElement).open) {
          setHasViewedOrganizedResult(true);
        }
      }}>
        <summary>整理結果を見る</summary>
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
                この内容で作成準備
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
                <strong>{chatReadiness.ready ? "提案書を作成できます" : "会話で必要情報を整理中"}</strong>
                <p>
                  {chatReadiness.ready
                    ? "不足項目は次回確認事項として扱い、このまま作成へ進めます。"
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
                {isLoading ? "作成中" : "今の内容で作成する"}
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
                <strong>最低限これだけ入れれば作成できます</strong>
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
                <p className="eyebrow">事前チェック</p>
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
                  <p className="warning-lead">不足があっても作成できます。精度を上げる場合は、以下の欄へ追記してください。</p>
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
              <span className="decision-pill rank-b">作成前整理</span>
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
                <p className="eyebrow">ヒアリングシート</p>
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
                <p className="eyebrow">議事録整理</p>
                <h3>ヒアリング結果整理</h3>
              </div>
              <span className={`decision-pill ${hearingResultSummary.hasInput ? "rank-a" : "rank-d"}`}>
                {hearingResultSummary.hasInput ? "作成済み" : "未入力"}
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
                <p className="eyebrow">競合分析</p>
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
                <p className="eyebrow">見積条件</p>
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
                <p className="eyebrow">見積AI</p>
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
            <p className="eyebrow">案件評価</p>
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
                <p className="eyebrow">業務改善の想定</p>
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
              <strong>提案書を作成</strong>
              <p>整理済みの内容からMarkdown・PPTX・PDFを作成します。</p>
              <button className="primary-button" type="submit" disabled={!canSubmit || !canGenerate}>
                {isLoading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Sparkles size={18} aria-hidden="true" />}
                {isLoading ? "作成中" : "提案書を作成"}
              </button>
            </div>
          </section>

          {!canSubmit && !isLoading && (
            <p className="submit-help">かんたん入力では「入力内容をAI用に整理」を押すと作成できます。詳細入力では案件概要を20文字以上入力してください。</p>
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

          <ProposalResultSection
            aiMinutes={aiMinutes}
            aiRecommendations={aiRecommendations}
            beautifulAiError={beautifulAiError}
            beautifulAiResult={beautifulAiResult}
            canCreateBeautifulAiOutput={canCreateBeautifulAiOutput}
            canDownloadMainOutputs={canDownloadMainOutputs}
            chatReadiness={chatReadiness}
            clearHistory={clearHistory}
            copyMarkdown={copyMarkdown}
            copyState={copyState}
            createBeautifulAiCurrent={createBeautifulAiCurrent}
            currentGuideStep={currentGuideStep}
            dealEvaluation={dealEvaluation}
            displayedMarkdown={displayedMarkdown}
            displayedProbability={displayedProbability}
            displayedWin={displayedWin}
            downloadEstimatePdfCurrent={downloadEstimatePdfCurrent}
            downloadEstimatePdfFor={downloadEstimatePdfFor}
            downloadMarkdown={downloadMarkdown}
            downloadPowerPoint={downloadPowerPoint}
            downloadPowerPointFor={downloadPowerPointFor}
            downloadSummaryPowerPoint={downloadSummaryPowerPoint}
            draftEmail={draftEmail}
            editablePreviewSlides={editablePreviewSlides}
            estimateSummary={estimateSummary}
            form={form}
            formatDateTime={formatDateTime}
            history={history}
            isBeautifulAiReady={isBeautifulAiReady}
            isCreatingBeautifulAi={isCreatingBeautifulAi}
            isDownloadingEstimatePdf={isDownloadingEstimatePdf}
            isDownloadingPowerPoint={isDownloadingPowerPoint}
            isDownloadingSummaryPowerPoint={isDownloadingSummaryPowerPoint}
            isGuideEnabled={isGuideEnabled}
            isLoading={isLoading}
            liveProjectSummary={liveProjectSummary}
            openBeautifulAiUrl={openBeautifulAiUrl}
            outputDigest={outputDigest}
            qualityScore={qualityScore}
            renderBeautifulAiDiagnosticsPanel={renderBeautifulAiDiagnosticsPanel}
            restoreHistory={restoreHistory}
            result={result}
            salesIndicators={salesIndicators}
            salesOpportunityScore={salesOpportunityScore}
            setShowEmailDraft={setShowEmailDraft}
            setShowMinutes={setShowMinutes}
            showEmailDraft={showEmailDraft}
            showMinutes={showMinutes}
            similarCases={similarCases}
            strategyCards={strategyCards}
            updatePreviewSlide={updatePreviewSlide}
            winRateImprovements={winRateImprovements}
          />
      </section>
      </details>

      )}

      <details className="future-integration-panel advanced-foldout" id="future-integration-panel" aria-label="今後の拡張予定">
        <summary>今後の拡張予定を開く</summary>
        <div className="section-heading">
          <p className="eyebrow">拡張予定</p>
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
      </details>

      {showGuideTutorial && (
        <div className="confirm-overlay guide-tutorial-overlay" role="dialog" aria-modal="true" aria-label="操作ガイド">
          <div className="confirm-modal guide-tutorial-modal">
            <div className="confirm-header">
              <div>
                <p className="eyebrow">3分ガイド</p>
                <h2>AI営業秘書の使い方</h2>
              </div>
              <button
                className="icon-button"
                type="button"
                onClick={() => {
                  window.localStorage.setItem(GUIDE_TUTORIAL_KEY, "true");
                  setShowGuideTutorial(false);
                }}
                title="閉じる"
              >
                <X size={18} aria-hidden="true" />
              </button>
            </div>
            <div className="tutorial-step-list">
              <article><span>1</span><strong>案件メールを貼る</strong></article>
              <article><span>2</span><strong>AIが整理する</strong></article>
              <article><span>3</span><strong>要約PPTをダウンロードする</strong></article>
              <article><span>4</span><strong>人が最終確認する</strong></article>
            </div>
            <div className="modal-actions">
              <button className="secondary-button" type="button" onClick={startSampleExperience}>
                まずはサンプルで体験
              </button>
              <button
                className="primary-button"
                type="button"
                onClick={() => {
                  window.localStorage.setItem(GUIDE_TUTORIAL_KEY, "true");
                  setShowGuideTutorial(false);
                }}
              >
                開始する
              </button>
            </div>
          </div>
        </div>
      )}

      {showPilotChecklist && currentUser && (
        <div className="pilot-checklist-overlay" role="dialog" aria-modal="true" aria-label="社内試験利用の確認">
          <div className="pilot-checklist-modal">
            <p className="eyebrow">社内試験利用</p>
            <h2>利用前に確認してください</h2>
            <ul>
              <li>顧客の機密情報を必要以上に入力しない</li>
              <li>AI出力は必ず人が確認する</li>
              <li>社外提出前に品質ゲートと上司レビューを確認する</li>
              <li>問題があればフィードバックを送る</li>
            </ul>
            <p className="status-note">確認日時のみ保存します。案件本文や顧客情報は保存しません。</p>
            <button
              className="primary-button"
              type="button"
              data-testid="pilot-checklist-confirm"
              onClick={() => void handleConfirmPilotChecklist()}
            >
              確認して開始する
            </button>
          </div>
        </div>
      )}

      {isConfirmOpen && (
        <div className="confirm-overlay" role="dialog" aria-modal="true" aria-label="作成前確認">
          <div className="confirm-modal">
            <div className="confirm-header">
              <div>
                <p className="eyebrow">確認</p>
                <h2>作成前の確認</h2>
              </div>
              <button className="icon-button" type="button" onClick={() => setIsConfirmOpen(false)} title="閉じる">
                <X size={18} aria-hidden="true" />
              </button>
            </div>

            <div className="confirm-easy-lead">
              <strong>この内容で作成できます</strong>
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
                  <strong>不足情報があります。作成は可能ですが、次回確認事項として反映します。</strong>
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
              <button className="primary-button confirm-generate-button" type="button" onClick={() => void generateProposal()} disabled={!canGenerate}>
                この内容で提案書を作成
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
    </AuthGate>
  );
}
