import { fetchJson } from "@/api/client";
import type { PromptExperiment, PromptExperimentAnalytics, PromptStudioDashboardData, PromptVersion, PromptWinnerRecommendation } from "@/types/app";

export type PromptVersionPayload = {
  prompt_name: string;
  version: string;
  description: string;
  target_agent: string;
  prompt_template: string;
  status: "draft" | "testing" | "active" | "archived";
};

export type PromptExperimentPayload = {
  experiment_name: string;
  target_prompt: string;
  control_version: string;
  candidate_version: string;
  traffic_ratio: number;
  status: "draft" | "testing" | "active" | "paused" | "completed" | "archived";
  start_at?: string;
  end_at?: string;
};

export function getPromptStudioDashboard(): Promise<{ dashboard: PromptStudioDashboardData }> {
  return fetchJson("/api/prompts/dashboard");
}

export function createPromptVersion(payload: PromptVersionPayload): Promise<{ prompt_version: PromptVersion; dashboard: PromptStudioDashboardData }> {
  return fetchJson("/api/prompts/versions", { method: "POST", body: JSON.stringify(payload) });
}

export function updatePromptVersionStatus(
  versionId: number,
  status: "draft" | "testing" | "active" | "archived"
): Promise<{ prompt_version: PromptVersion; dashboard: PromptStudioDashboardData }> {
  return fetchJson(`/api/prompts/versions/${versionId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status })
  });
}

export function rollbackPromptVersion(promptName: string, version: string): Promise<{ prompt_version: PromptVersion; dashboard: PromptStudioDashboardData }> {
  return fetchJson("/api/prompts/rollback", {
    method: "POST",
    body: JSON.stringify({ prompt_name: promptName, version })
  });
}

export function createPromptExperiment(payload: PromptExperimentPayload): Promise<{ experiment: PromptExperiment; dashboard: PromptStudioDashboardData }> {
  return fetchJson("/api/prompts/experiments", { method: "POST", body: JSON.stringify(payload) });
}

export function judgePromptExperiment(experimentId: number): Promise<{ recommendation: PromptWinnerRecommendation; dashboard: PromptStudioDashboardData }> {
  return fetchJson(`/api/prompts/experiments/${experimentId}/judge`, { method: "POST" });
}

export function createPromptExperimentFromLearning(improvementId: number): Promise<{ result: unknown; dashboard: PromptStudioDashboardData }> {
  return fetchJson(`/api/prompts/from-learning/${improvementId}`, { method: "POST" });
}

export function routePromptVersion(promptName: string, projectId?: number): Promise<{
  routing: {
    prompt_name: string;
    version: string;
    experiment_id: number | null;
    experiment_name: string;
    prompt_template: string;
    target_agent: string;
    reason: string;
  };
}> {
  return fetchJson("/api/prompts/route", {
    method: "POST",
    body: JSON.stringify({ prompt_name: promptName, project_id: projectId })
  });
}

export function recordPromptMetric(payload: {
  experiment_id?: number | null;
  prompt_name: string;
  prompt_version: string;
  project_id?: number | null;
  outcome?: "won" | "lost" | "pending" | "unknown" | "";
  review_count?: number;
  quality_gate_passed?: boolean;
  proposal_time_seconds?: number;
  user_rating?: string;
}): Promise<{ metric: unknown; analytics: PromptExperimentAnalytics }> {
  return fetchJson("/api/prompts/metrics", { method: "POST", body: JSON.stringify(payload) });
}
