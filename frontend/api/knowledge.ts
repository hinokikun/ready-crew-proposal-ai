import { fetchJson } from "@/api/client";
import type {
  KnowledgeBestPractices,
  KnowledgeApprovalStatus,
  KnowledgeEvaluationStatus,
  KnowledgeOutcome,
  KnowledgeSourceType,
  KnowledgeSearchInsights,
  ProposalKnowledgeEntry,
  ProposalTemplateCategory,
  ProposalTemplateEntry
} from "@/types/app";

export type CreateKnowledgePayload = {
  industry?: string;
  company_size?: string;
  project_summary: string;
  adopted_proposal?: string;
  proposal_story?: string;
  adoption_reason?: string;
  lost_reason?: string;
  result?: string;
  owner_memo?: string;
  outcome?: KnowledgeOutcome;
  rating?: number;
  evaluation_status?: KnowledgeEvaluationStatus;
  tags?: string;
  approval_status?: KnowledgeApprovalStatus;
  source_type?: KnowledgeSourceType;
  source_note?: string;
};

export type CreateTemplatePayload = {
  category: ProposalTemplateCategory;
  title: string;
  template_summary?: string;
  structure?: string;
  recommended_for?: string;
  is_active?: boolean;
};

export function getKnowledgeEntries(limit = 20, offset = 0): Promise<{ entries: ProposalKnowledgeEntry[] }> {
  return fetchJson(`/api/knowledge/entries?limit=${limit}&offset=${offset}`);
}

export function createKnowledgeEntry(payload: CreateKnowledgePayload): Promise<{ entry: ProposalKnowledgeEntry }> {
  return fetchJson("/api/knowledge/entries", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateKnowledgeEvaluation(
  entryId: number,
  payload: { rating: number; evaluation_status: KnowledgeEvaluationStatus }
): Promise<{ entry: ProposalKnowledgeEntry }> {
  return fetchJson(`/api/knowledge/entries/${entryId}/evaluation`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function updateKnowledgeStatus(
  entryId: number,
  approvalStatus: KnowledgeApprovalStatus
): Promise<{ entry: ProposalKnowledgeEntry }> {
  return fetchJson(`/api/knowledge/entries/${entryId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ approval_status: approvalStatus })
  });
}

export function recalculateKnowledgeQuality(entryId: number): Promise<{ entry: ProposalKnowledgeEntry }> {
  return fetchJson(`/api/knowledge/entries/${entryId}/quality/recalculate`, {
    method: "POST"
  });
}

export function searchKnowledge(payload: {
  project_summary: string;
  industry?: string;
  limit?: number;
}): Promise<{ insights: KnowledgeSearchInsights }> {
  return fetchJson("/api/knowledge/search", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getKnowledgeBestPractices(): Promise<{ best_practices: KnowledgeBestPractices }> {
  return fetchJson("/api/knowledge/best-practices");
}

export function getProposalTemplates(
  category = "",
  includeInactive = false,
  limit = 50,
  offset = 0
): Promise<{ templates: ProposalTemplateEntry[] }> {
  const params = new URLSearchParams({
    category,
    include_inactive: String(includeInactive),
    limit: String(limit),
    offset: String(offset)
  });
  return fetchJson(`/api/knowledge/templates?${params.toString()}`);
}

export function createProposalTemplate(payload: CreateTemplatePayload): Promise<{ template: ProposalTemplateEntry }> {
  return fetchJson("/api/knowledge/templates", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateProposalTemplateActive(templateId: number, isActive: boolean): Promise<{ template: ProposalTemplateEntry }> {
  return fetchJson(`/api/knowledge/templates/${templateId}`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive })
  });
}
