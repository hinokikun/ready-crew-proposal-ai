import type { AnalysisResponse, ProposalRequest } from "@/types/proposal";
import type { AuditLog, CrmCustomer, CrmProject, ManagedUser, UserRole } from "@/types/app";
import { getAuthHeaders } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";

export type { AuditLog, CrmCustomer, CrmProject, ManagedUser } from "@/types/app";

export type CompanyResearchApiResponse = {
  source_url: string;
  fetched: boolean;
  overview: string;
  competitors: string[];
  recruitment: string;
  news: string[];
  services: string[];
  sns: string[];
};

export async function analyzeProposal(payload: ProposalRequest): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    let message = `分析に失敗しました。status=${response.status}`;

    try {
      const errorBody = (await response.json()) as { detail?: string };
      if (errorBody.detail) {
        message = `${message}: ${errorBody.detail}`;
      }
    } catch {
      message = `${message}: バックエンドからエラー詳細を取得できませんでした。`;
    }

    throw new Error(message);
  }

  return response.json() as Promise<AnalysisResponse>;
}

export async function researchCompanyUrl(payload: {
  url: string;
  project_brief: string;
  client_company_info: string;
}): Promise<CompanyResearchApiResponse> {
  const response = await fetch(`${API_BASE_URL}/api/company-research`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    let message = `会社URL調査に失敗しました。status=${response.status}`;

    try {
      const errorBody = (await response.json()) as { detail?: string };
      if (errorBody.detail) {
        message = `${message}: ${errorBody.detail}`;
      }
    } catch {
      message = `${message}: バックエンドからエラー詳細を取得できませんでした。`;
    }

    throw new Error(message);
  }

  return response.json() as Promise<CompanyResearchApiResponse>;
}

export async function listUsers(): Promise<{ users: ManagedUser[] }> {
  return fetchJson("/api/users");
}

export async function createUser(payload: { email: string; password: string; role: UserRole }): Promise<{ user: ManagedUser }> {
  return fetchJson("/api/users", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateUserActive(userId: number, isActive: boolean): Promise<{ user: ManagedUser }> {
  return fetchJson(`/api/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive })
  });
}

export async function getCrm(): Promise<{ customers: CrmCustomer[]; projects: CrmProject[] }> {
  return fetchJson("/api/projects/crm");
}

export async function getDbLogs(): Promise<{ logs: Array<Record<string, string | number | null>> }> {
  return fetchJson("/api/logs");
}

export async function getAuditLogs(): Promise<{ logs: AuditLog[] }> {
  return fetchJson("/api/logs/audit");
}

export async function saveUsageLogToBackend(payload: {
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

async function fetchJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...(init.headers ?? {})
    }
  });

  if (!response.ok) {
    let message = `APIリクエストに失敗しました。status=${response.status}`;
    try {
      const errorBody = (await response.json()) as { detail?: string };
      if (errorBody.detail) message = `${message}: ${errorBody.detail}`;
    } catch {
      message = `${message}: バックエンドからエラー詳細を取得できませんでした。`;
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

