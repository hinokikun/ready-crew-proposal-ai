import { fetchJson } from "@/client-api/client";
import type {
  ProposalBestPractice,
  ProposalImprovementBacklogItem,
  ProposalOptimizationDashboard,
  ProposalOptimizationData
} from "@/types/app";

export function runProposalOptimization(projectId = ""): Promise<ProposalOptimizationData> {
  return fetchJson("/api/proposal-optimization/run", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId })
  });
}

export function getProposalOptimizationRecommendations(projectId = ""): Promise<ProposalOptimizationData> {
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  const query = params.toString();
  return fetchJson(`/api/proposal-optimization/recommendations${query ? `?${query}` : ""}`);
}

export function updateProposalOptimizationStatus(
  backlogId: number,
  status: string
): Promise<{ item: ProposalImprovementBacklogItem }> {
  return fetchJson(`/api/proposal-optimization/backlog/${backlogId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status })
  });
}

export function updateProposalOptimizationMeasurement(
  backlogId: number,
  payload: {
    measurement_status: string;
    measured_effect?: Record<string, unknown>;
    measurement_period?: string;
    outcome_type?: string;
  }
): Promise<{ item: ProposalImprovementBacklogItem }> {
  return fetchJson(`/api/proposal-optimization/backlog/${backlogId}/measurement`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function approveProposalOptimizationItem(backlogId: number): Promise<{ item: ProposalImprovementBacklogItem }> {
  return fetchJson(`/api/proposal-optimization/backlog/${backlogId}/approve`, {
    method: "PATCH",
    body: JSON.stringify({})
  });
}

export function getProposalOptimizationDashboard(): Promise<{ dashboard: ProposalOptimizationDashboard }> {
  return fetchJson("/api/proposal-optimization/dashboard");
}

export function getProposalBestPractices(): Promise<{ best_practices: ProposalBestPractice[] }> {
  return fetchJson("/api/proposal-optimization/best-practices");
}

export function extractProposalBestPractices(): Promise<{ best_practices: ProposalBestPractice[] }> {
  return fetchJson("/api/proposal-optimization/best-practices/extract", {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function updateProposalBestPracticeStatus(
  bestPracticeId: number,
  payload: { status: string; reason?: string }
): Promise<{ best_practice: ProposalBestPractice }> {
  return fetchJson(`/api/proposal-optimization/best-practices/${bestPracticeId}/status`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function getProposalOptimizationRevisionActions(projectId = ""): Promise<{ selected_actions: Array<Record<string, unknown>> }> {
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  const query = params.toString();
  return fetchJson(`/api/proposal-optimization/revision-actions${query ? `?${query}` : ""}`);
}

export function markProposalOptimizationInRevision(backlogIds: number[]): Promise<{ items: ProposalImprovementBacklogItem[] }> {
  return fetchJson("/api/proposal-optimization/revision-actions", {
    method: "POST",
    body: JSON.stringify({ backlog_ids: backlogIds })
  });
}
