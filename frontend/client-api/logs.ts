import { fetchBlob, fetchJson } from "@/client-api/client";
import type {
  AuditLog,
  CreationHistoryItem,
  ImprovementDashboardData,
  OperationReadinessData,
  TrialReportData,
  UsageDashboardData
} from "@/types/app";

export function getDbLogs(): Promise<{ logs: Array<Record<string, string | number | null>> }> {
  return fetchJson("/api/logs");
}

export function getAuditLogs(): Promise<{ logs: AuditLog[] }> {
  return fetchJson("/api/logs/audit");
}

export function getUsageDashboard(): Promise<{ dashboard: UsageDashboardData }> {
  return fetchJson("/api/logs/usage-dashboard");
}

export function getCreationHistory(params: {
  q?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
} = {}): Promise<{ items: CreationHistoryItem[] }> {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  });
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return fetchJson(`/api/logs/creation-history${suffix}`);
}

export function downloadUsageDashboardCsv(): Promise<Blob> {
  return fetchBlob("/api/logs/usage-dashboard.csv");
}

export function createTrialReport(payload: { admin_comment: string }): Promise<{ report: TrialReportData }> {
  return fetchJson("/api/logs/trial-report", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getOperationReadiness(): Promise<{ readiness: OperationReadinessData }> {
  return fetchJson("/api/logs/operation-readiness");
}

export function getImprovementDashboard(): Promise<{ dashboard: ImprovementDashboardData }> {
  return fetchJson("/api/logs/improvement-dashboard");
}

export function saveUsageLogToBackend(payload: {
  feature_name: string;
  input_length: number;
  output_type: string;
  status: "success" | "failure";
  error_type?: string;
}): Promise<{ ok: boolean }> {
  return fetchJson("/api/logs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
