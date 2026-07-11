import { fetchJson } from "@/client-api/client";
import type {
  AuthUser,
  PilotDashboardData,
  PilotEndReport,
  PilotIssue,
  PilotIssueSeverity,
  PilotIssueStatus,
  PilotMaintenanceState,
  PilotRetentionPreview,
  PilotStatus
} from "@/types/app";

export function getPilotStatus(): Promise<{ pilot: PilotStatus }> {
  return fetchJson("/api/pilot/status");
}

export function confirmPilotChecklist(): Promise<{ user: AuthUser; ok: boolean }> {
  return fetchJson("/api/pilot/checklist-confirmed", {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function getPilotDashboard(): Promise<{ dashboard: PilotDashboardData }> {
  return fetchJson("/api/pilot/dashboard");
}

export type PilotIssuePayload = {
  category: string;
  severity: PilotIssueSeverity;
  title: string;
  summary?: string;
  reproduction_steps?: string;
  assigned_to?: string;
};

export type PilotIssueUpdatePayload = Partial<PilotIssuePayload> & {
  status?: PilotIssueStatus;
  resolution_note?: string;
};

export function getPilotIssues(): Promise<{ issues: PilotIssue[] }> {
  return fetchJson("/api/pilot/issues");
}

export function createPilotIssue(payload: PilotIssuePayload): Promise<{ issue: PilotIssue }> {
  return fetchJson("/api/pilot/issues", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updatePilotIssue(issueId: string, payload: PilotIssueUpdatePayload): Promise<{ issue: PilotIssue }> {
  return fetchJson(`/api/pilot/issues/${encodeURIComponent(issueId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function createPilotIssueFromFeedback(
  feedbackId: number,
  payload: Pick<PilotIssuePayload, "category" | "severity" | "title" | "assigned_to">
): Promise<{ issue: PilotIssue; duplicate_candidates: Array<Partial<PilotIssue>> }> {
  return fetchJson(`/api/pilot/issues/from-feedback/${feedbackId}`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updatePilotMaintenance(enabled: boolean, reason: string): Promise<{ maintenance: PilotMaintenanceState }> {
  return fetchJson("/api/pilot/maintenance", {
    method: "PATCH",
    body: JSON.stringify({ enabled, reason })
  });
}

export function previewPilotDataRetention(): Promise<{ preview: PilotRetentionPreview }> {
  return fetchJson("/api/pilot/data-retention/preview");
}

export function applyPilotDataRetention(
  action: "keep_summary_only" | "anonymize_events" | "delete_events" | "anonymize_feedback" | "disable_test_users",
  confirmText: string
): Promise<{ action: string; before: PilotRetentionPreview; after: PilotRetentionPreview }> {
  return fetchJson("/api/pilot/data-retention", {
    method: "POST",
    body: JSON.stringify({ action, confirm_text: confirmText })
  });
}

export function endPilot(adminComment: string): Promise<{ report: PilotEndReport }> {
  return fetchJson("/api/pilot/end", {
    method: "POST",
    body: JSON.stringify({ admin_comment: adminComment })
  });
}
