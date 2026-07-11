import { fetchJson } from "@/client-api/client";
import type { ActionQueueItem, OrchestratorAnalytics, OrchestratorStatus } from "@/types/app";

export function getActionQueue(params: { status?: string; limit?: number } = {}): Promise<{ queue: ActionQueueItem[] }> {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  return fetchJson(`/api/orchestrator/queue${query ? `?${query}` : ""}`);
}

export function getProjectOrchestratorStatus(projectId: number): Promise<{ orchestrator: OrchestratorStatus }> {
  return fetchJson(`/api/orchestrator/projects/${projectId}/status`);
}

export function startProjectOrchestrator(projectId: number): Promise<{ orchestrator: { created: number; project_id: number; queue: ActionQueueItem[] } }> {
  return fetchJson(`/api/orchestrator/projects/${projectId}/start`, { method: "POST" });
}

export function runProjectOrchestrator(projectId: number): Promise<{ orchestrator: OrchestratorStatus & { executed: number } }> {
  return fetchJson(`/api/orchestrator/projects/${projectId}/run`, { method: "POST" });
}

export function retryQueueAction(actionId: number): Promise<{ action: ActionQueueItem }> {
  return fetchJson(`/api/orchestrator/actions/${actionId}/retry`, { method: "POST" });
}

export function getOrchestratorAnalytics(): Promise<{ orchestrator: OrchestratorAnalytics }> {
  return fetchJson("/api/orchestrator/analytics");
}
