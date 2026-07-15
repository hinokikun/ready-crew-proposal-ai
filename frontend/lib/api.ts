export type {
  AuditLog,
  AiNotification,
  AiNotificationAnalytics,
  AiNotificationCenterData,
  AiNotificationPriority,
  AiNotificationStatus,
  AiNotificationSummary,
  ActionQueueItem,
  ActionQueueStatus,
  CreationHistoryItem,
  CrmCustomer,
  CrmProject,
  DailyBriefingAnalytics,
  DailyBriefingAgentComment,
  DailyBriefingData,
  DailyBriefingSuggestion,
  DailyBriefingSummary,
  DailyBriefingTimelineItem,
  FeedbackEntry,
  FeedbackRating,
  FeedbackSummary,
  PilotDashboardData,
  PilotEndReport,
  PilotFeedbackMetrics,
  PilotFeedbackPreview,
  PilotIncident,
  PilotIssue,
  PilotIssueSeverity,
  PilotIssueStatus,
  PilotJudgment,
  PilotMaintenanceState,
  PilotRetentionPreview,
  PilotStatus,
  ConnectorReadinessItem,
  DryRunLog,
  ExternalIntakeCandidate,
  ExternalIntakeSourceType,
  ImprovementDashboardData,
  IntegrationDryRunResult,
  IntegrationDryRunTemplate,
  IntegrationAnalytics,
  IntegrationSetting,
  IntegrationStatus,
  LearningAnalytics,
  LearningDashboardData,
  LearningImprovement,
  LearningRun,
  LearningSimulation,
  ManagedUser,
  OperationReadinessData,
  OperationReadinessStatus,
  OrchestratorAnalytics,
  OrchestratorStatus,
  PromptExperiment,
  PromptExperimentAnalytics,
  PromptMetricSummary,
  PromptStudioDashboardData,
  PromptVersion,
  PromptVersionStatus,
  PromptWinnerRecommendation,
  KnowledgeBestPractices,
  KnowledgeSearchInsights,
  PresentationAnalytics,
  ProposalBestPractice,
  ProposalImprovementBacklogItem,
  ProposalOptimizationDashboard,
  ProposalOptimizationData,
  PresentationImprovement,
  PresentationReview,
  PresentationReviewIssue,
  PresentationReviewScore,
  PresentationRevision,
  PresentationRevisionChange,
  ProductAnalyticsDashboardData,
  ProjectHandoff,
  ProjectLifecycleAnalytics,
  ProjectLifecycleDetail,
  ProjectLifecycleEvent,
  ProjectLifecycleStatus,
  ProjectLostReason,
  ProjectOutcome,
  ProjectRetrospective,
  ProposalKnowledgeEntry,
  ProposalTemplateEntry,
  ReleaseNoteEntry,
  TrialReportData,
  UsageDashboardData,
  UserRole,
  ProposalReviewEntry,
  ProposalReviewRevision,
  ProposalReviewStatus,
  QualityGateRecord,
  ReleaseRecord,
  ReleaseRecordStatus,
  WorkspaceConversationRecord,
  WorkspaceContext,
  WorkspaceContextItem,
  WorkspaceSummary,
  WorkspaceWorkLogRecord
} from "@/types/app";

export { analyzeProposal, researchCompanyUrl, type CompanyResearchApiResponse } from "@/client-api/proposal";
export { getTodayBriefing, saveBriefingEvent } from "@/client-api/briefing";
export {
  archiveAiNotification,
  getAiNotifications,
  markAiNotificationActioned,
  markAiNotificationRead,
  runAiWatchEngine
} from "@/client-api/notifications";
export { changeOwnPassword, createUser, deleteUser, listUsers, updateUser, updateUserActive, updateUserPilot } from "@/client-api/users";
export {
  completeProject,
  createProject,
  generateProjectHandoff,
  getCrm,
  getProjectLifecycle,
  getProjectLifecycleAnalytics,
  registerProjectOutcome,
  updateProjectStatus,
  type ProjectCompletePayload,
  type ProjectCreatePayload,
  type ProjectHandoffPayload
} from "@/client-api/crm";
export {
  createTrialReport,
  downloadUsageDashboardCsv,
  getAuditLogs,
  getCreationHistory,
  getDbLogs,
  getImprovementDashboard,
  getOperationReadiness,
  getUsageDashboard,
  saveUsageLogToBackend
} from "@/client-api/logs";
export { getFeedback, submitFeedback } from "@/client-api/feedback";
export {
  applyPilotDataRetention,
  confirmPilotChecklist,
  createPilotIssue,
  createPilotIssueFromFeedback,
  endPilot,
  getPilotDashboard,
  getPilotIssues,
  getPilotStatus,
  previewPilotDataRetention,
  updatePilotIssue,
  updatePilotMaintenance
} from "@/client-api/pilot";
export {
  convertExternalIntakeCandidate,
  createExternalIntake,
  getExternalIntakeCandidates,
  getConnectorReadiness,
  getIntegrationDryRunLogs,
  getIntegrationSettings,
  reviewExternalIntakeCandidate,
  runIntegrationDryRun,
  updateIntegrationSetting,
  type ExternalIntakePayload,
  type IntegrationSettingPayload
} from "@/client-api/integrations";
export {
  createReleaseNote,
  getProductAnalyticsDashboard,
  getReleaseNotes,
  saveProductAnalyticsEvent,
  updateProductAnalyticsErrorResolved
} from "@/client-api/analytics";
export { getLearningDashboard, runLearningAnalysis, updateLearningImprovementStatus } from "@/client-api/learning";
export {
  createPromptExperiment,
  createPromptExperimentFromLearning,
  createPromptVersion,
  getPromptStudioDashboard,
  judgePromptExperiment,
  recordPromptMetric,
  rollbackPromptVersion,
  routePromptVersion,
  updatePromptVersionStatus,
  type PromptExperimentPayload,
  type PromptVersionPayload
} from "@/client-api/prompts";
export {
  getActionQueue,
  getOrchestratorAnalytics,
  getProjectOrchestratorStatus,
  retryQueueAction,
  runProjectOrchestrator,
  startProjectOrchestrator
} from "@/client-api/orchestrator";
export {
  createKnowledgeEntry,
  createProposalTemplate,
  getKnowledgeBestPractices,
  getKnowledgeEntries,
  getProposalTemplates,
  recalculateKnowledgeQuality,
  searchKnowledge,
  updateKnowledgeEvaluation,
  updateKnowledgeStatus,
  updateProposalTemplateActive,
  type CreateKnowledgePayload,
  type CreateTemplatePayload
} from "@/client-api/knowledge";
export {
  getWorkspaceConversation,
  getWorkspaceSummary,
  saveWorkspaceConversation,
  type WorkspaceConversationPayload
} from "@/client-api/workspace";
export { getWorkspaceContext, switchWorkspaceContext } from "@/client-api/organizations";
export {
  approvePresentationRevision,
  comparePresentationRevisions,
  createPresentationReview,
  createPresentationRevision,
  generateBeautifulAiRevision,
  getPresentationReviewTimeline,
  rejectPresentationRevision,
  type PresentationReviewPayload
} from "@/client-api/presentationReview";
export {
  approveProposalOptimizationItem,
  extractProposalBestPractices,
  getProposalBestPractices,
  getProposalOptimizationDashboard,
  getProposalOptimizationRecommendations,
  getProposalOptimizationRevisionActions,
  markProposalOptimizationInRevision,
  runProposalOptimization,
  updateProposalBestPracticeStatus,
  updateProposalOptimizationMeasurement,
  updateProposalOptimizationStatus
} from "@/client-api/proposalOptimization";
export {
  applyReviewFeedback,
  getProposalReview,
  getProposalReviewRevisions,
  listProposalReviews,
  rerequestProposalReview,
  requestProposalReview,
  updateProposalReview
} from "@/client-api/reviews";
export { bypassQualityGate, completeQualityGate, getQualityGate, saveQualityGate } from "@/client-api/qualityGates";
export { createReleaseRecord, getReleases, publishReleaseRecord, updateReleaseRecord, type ReleaseRecordPayload } from "@/client-api/releases";
