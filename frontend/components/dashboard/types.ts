import type { AuditLog, CrmProject, FeedbackSummary, UsageDashboardData } from "@/types/app";
import type { UsageLogEntry } from "@/lib/storage";

export type OperationsHistoryEntry = {
  id: string;
  createdAt: string;
  title: string;
  clientName: string;
};

export type OperationsDashboardInput = {
  projects: CrmProject[];
  history: OperationsHistoryEntry[];
  usageLogs: UsageLogEntry[];
  auditLogs: AuditLog[];
  usageDashboard: UsageDashboardData | null;
  feedbackSummary: FeedbackSummary;
  qualityGateWaiting: boolean;
  hasProposalResult: boolean;
};

export type ExecutiveMetric = {
  label: string;
  value: string;
  note: string;
  tone?: "normal" | "warning" | "danger" | "success";
};

export type ActionItem = {
  id: string;
  priority: "high" | "medium" | "low";
  stars: string;
  title: string;
  detail: string;
  actionLabel: string;
  targetPanelId: string;
};

export type ActivityItem = {
  id: string;
  agent: string;
  title: string;
  detail: string;
  time: string;
};

export type KpiMetric = {
  label: string;
  value: string;
  note: string;
};

export type QuickAction = {
  label: string;
  target: string;
  adminOnly?: boolean;
};

export type OperationsDashboardData = {
  executiveMetrics: ExecutiveMetric[];
  actionItems: ActionItem[];
  activities: ActivityItem[];
  kpiMetrics: KpiMetric[];
  quickActions: QuickAction[];
};
