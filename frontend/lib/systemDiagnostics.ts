import { getAuthHeaders } from "@/lib/auth";
import { fetchJson } from "@/client-api/client";
import { API_BASE_URL } from "@/lib/config";

export type SystemDiagnosticStatus = "ok" | "warning" | "error" | "skipped" | "unknown";
export type EnvironmentCheckStatus = "configured" | "missing" | "invalid" | "disabled" | "optional" | "unknown";

export type SystemDiagnosticCheck = {
  name: string;
  label?: string;
  status: SystemDiagnosticStatus;
  message: string;
  duration_ms?: number;
  action?: string;
};

export type SystemDiagnostics = {
  overall_status: SystemDiagnosticStatus;
  backend: {
    reachable: boolean;
    version: string;
  };
  database: {
    connected: boolean;
  };
  auth: {
    available: boolean;
  };
  openai: {
    enabled: boolean;
    configured: boolean;
  };
  beautiful_ai: {
    enabled: boolean;
    configured: boolean;
    mock: boolean;
    api_reachable: boolean;
    api_mode: string;
  };
  frontend: {
    api_base_url: string;
  };
  checks: SystemDiagnosticCheck[];
};

export type SystemCheckRun = {
  overall_status: SystemDiagnosticStatus;
  summary: {
    total: number;
    ok: number;
    warning: number;
    error: number;
    skipped: number;
    unknown: number;
  };
  started_at: string;
  completed_at: string;
  duration_ms: number;
  checks: SystemDiagnosticCheck[];
};

export type EnvironmentCheckItem = {
  name: string;
  status: EnvironmentCheckStatus;
  required: boolean;
  category: "required" | "recommended" | "optional" | string;
  source: string;
  message: string;
  action: string;
};

export type EnvironmentChecks = {
  items: EnvironmentCheckItem[];
  summary: {
    total: number;
    configured: number;
    missing: number;
    invalid: number;
    optional: number;
  };
};

export type AdminAiLogItem = {
  id: string;
  source: string;
  created_at: string;
  provider: string;
  operation: string;
  status: string;
  user_id?: number | null;
  user: string;
  project_id: string;
  project: string;
  duration_ms: number;
  request_id: string;
  error_type: string;
  retry_count: number;
  summary: string;
};

export type ProposalGenerationHistoryItem = {
  id: number;
  created_at: string;
  user_id?: number | null;
  user: string;
  project_id: string;
  project_title: string;
  output_type: string;
  provider: string;
  status: string;
  duration_ms: number;
  error_type: string;
  downloadable: boolean;
  external_url_available: boolean;
  open_url: string;
  summary: string;
};

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export async function getSystemDiagnostics() {
  const response = await fetch(`${API_BASE_URL}/api/system/diagnostics`, {
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-Frontend-Api-Base-Url": API_BASE_URL,
      ...getAuthHeaders()
    }
  });
  if (!response.ok) {
    throw new Error(`SYSTEM_DIAGNOSTICS_FAILED status=${response.status}`);
  }
  return response.json() as Promise<SystemDiagnostics>;
}

export async function runSystemSelfCheck() {
  return fetchJson<SystemCheckRun>("/api/system/self-check", { method: "POST" });
}

export async function runConnectionTests(checks: string[] = []) {
  return fetchJson<SystemCheckRun>("/api/system/connection-tests", {
    method: "POST",
    body: JSON.stringify({ checks })
  });
}

export async function getEnvironmentChecks() {
  const response = await fetch(`${API_BASE_URL}/api/system/environment`, {
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-Frontend-Api-Base-Url": API_BASE_URL,
      ...getAuthHeaders()
    }
  });
  if (!response.ok) {
    throw new Error(`SYSTEM_ENVIRONMENT_FAILED status=${response.status}`);
  }
  return response.json() as Promise<EnvironmentChecks>;
}

export async function getAdminAiLogs(page = 1, pageSize = 20) {
  return fetchJson<PaginatedResponse<AdminAiLogItem>>(`/api/admin/ai-logs?page=${page}&page_size=${pageSize}`);
}

export async function getProposalGenerationHistory(page = 1, pageSize = 20) {
  return fetchJson<PaginatedResponse<ProposalGenerationHistoryItem>>(
    `/api/admin/proposal-generation-history?page=${page}&page_size=${pageSize}`
  );
}
