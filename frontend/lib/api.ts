import type { AnalysisResponse, ProposalRequest } from "@/types/proposal";
import { API_BASE_URL } from "@/lib/config";

export async function analyzeProposal(payload: ProposalRequest): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
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


