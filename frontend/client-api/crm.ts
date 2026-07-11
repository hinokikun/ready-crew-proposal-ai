import { fetchJson } from "@/client-api/client";
import type { CrmCustomer, CrmProject, ProjectLifecycleDetail, ProjectLifecycleStatus, ProjectLostReason } from "@/types/app";

export function getCrm(): Promise<{ customers: CrmCustomer[]; projects: CrmProject[] }> {
  return fetchJson("/api/projects/crm");
}

export type ProjectCreatePayload = {
  customer_name: string;
  project_name: string;
  summary?: string;
  win_probability?: number;
  next_action?: string;
};

export type ProjectHandoffPayload = {
  proposal_summary?: string;
  cautions?: string;
  deadline?: string;
  owner?: string;
  special_functions?: string;
  cms?: string;
};

export type ProjectCompletePayload = {
  success_factors?: string;
  improvements?: string;
  next_learnings?: string;
};

export function createProject(payload: ProjectCreatePayload): Promise<{ lifecycle: ProjectLifecycleDetail }> {
  return fetchJson("/api/projects", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getProjectLifecycle(projectId: number): Promise<{ lifecycle: ProjectLifecycleDetail }> {
  return fetchJson(`/api/projects/${projectId}/lifecycle`);
}

export function updateProjectStatus(
  projectId: number,
  payload: { status: ProjectLifecycleStatus; note?: string }
): Promise<{ lifecycle: ProjectLifecycleDetail }> {
  return fetchJson(`/api/projects/${projectId}/status`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function registerProjectOutcome(
  projectId: number,
  payload: { outcome: "won" | "lost"; lost_reason?: ProjectLostReason; note?: string }
): Promise<{ lifecycle: ProjectLifecycleDetail }> {
  return fetchJson(`/api/projects/${projectId}/outcome`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function generateProjectHandoff(projectId: number, payload: ProjectHandoffPayload): Promise<{ lifecycle: ProjectLifecycleDetail }> {
  return fetchJson(`/api/projects/${projectId}/handoff`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function completeProject(projectId: number, payload: ProjectCompletePayload): Promise<{ lifecycle: ProjectLifecycleDetail }> {
  return fetchJson(`/api/projects/${projectId}/complete`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getProjectLifecycleAnalytics() {
  return fetchJson("/api/projects/lifecycle/analytics");
}
