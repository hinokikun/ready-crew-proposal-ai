import { fetchJson } from "@/api/client";
import type { WorkspaceConversationRecord, WorkspaceSummary, WorkspaceWorkLogRecord } from "@/types/app";

export type WorkspaceConversationPayload = {
  project_id: string;
  conversations: Array<{
    client_message_id: string;
    agent_name: string;
    message_type: string;
    message_body: string;
    status: string;
  }>;
  work_logs: Array<{
    client_log_id: string;
    agent_name: string;
    action_summary: string;
    status: string;
  }>;
};

export function saveWorkspaceConversation(payload: WorkspaceConversationPayload): Promise<{
  ok: boolean;
  project_id: string;
  saved_conversations: number;
  saved_logs: number;
}> {
  return fetchJson("/api/workspace/conversations", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getWorkspaceConversation(projectId: string): Promise<{
  project_id: string;
  conversations: WorkspaceConversationRecord[];
  work_logs: WorkspaceWorkLogRecord[];
}> {
  return fetchJson(`/api/workspace/conversations/${encodeURIComponent(projectId)}`);
}

export function getWorkspaceSummary(projectId: string): Promise<{ summary: WorkspaceSummary }> {
  return fetchJson(`/api/workspace/summary/${encodeURIComponent(projectId)}`);
}
