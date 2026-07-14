import { fetchJson } from "@/client-api/client";
import type { WorkspaceContext } from "@/types/app";

export function getWorkspaceContext(): Promise<WorkspaceContext> {
  return fetchJson("/api/organizations/context");
}

export function switchWorkspaceContext(payload: { organization_id: number; workspace_id: number }): Promise<{ current: WorkspaceContext["current"] }> {
  return fetchJson("/api/organizations/context", {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}
