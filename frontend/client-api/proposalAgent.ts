import { fetchBlob, fetchJson } from "@/client-api/client";
import type { ProposalAgentDashboardData, ProposalAgentMemory } from "@/types/app";

export type ProposalAgentMemoryPayload = {
  project_id?: number | null;
  project_name: string;
  hearing_notes: string;
  confirmation_items: string;
  proposal_content: string;
  competitor_analysis: string;
  improvement_history: string;
};

export function getProposalAgentDashboard(): Promise<{ dashboard: ProposalAgentDashboardData }> {
  return fetchJson("/api/proposal-agent/dashboard");
}

export function saveProposalAgentMemory(payload: ProposalAgentMemoryPayload): Promise<{ memory: ProposalAgentMemory }> {
  return fetchJson("/api/proposal-agent/memory", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function downloadProposalAgentDashboard(format: "markdown" | "csv" | "pdf" | "pptx"): Promise<Blob> {
  return fetchBlob(`/api/proposal-agent/dashboard/export?format=${format}`);
}
