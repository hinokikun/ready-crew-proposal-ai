import type { AnalysisResponse, ProposalRequest } from "@/types/proposal";
import { getAuthHeaders } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";

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

