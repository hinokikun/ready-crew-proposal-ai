import type { AnalysisResponse, ProposalRequest } from "@/types/proposal";
import { fetchJson } from "@/api/client";

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

export function analyzeProposal(payload: ProposalRequest): Promise<AnalysisResponse> {
  return fetchJson("/api/analyze", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function researchCompanyUrl(payload: {
  url: string;
  project_brief: string;
  client_company_info: string;
}): Promise<CompanyResearchApiResponse> {
  return fetchJson("/api/company-research", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
