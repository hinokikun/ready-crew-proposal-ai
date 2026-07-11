export type AiWorkspaceAgentKey = "secretary" | "sales" | "director" | "pm" | "president";
export type AgentStatus = "waiting" | "active" | "done";

export type AgentContent = {
  key: AiWorkspaceAgentKey;
  name: string;
  role: string;
  iconLabel: string;
  colorClass: string;
  headline: string;
  task: string;
  comment: string;
  activeComment: string;
  doneComment: string;
  chatMessage: string;
  activeLog: string;
  rerunLabel: string;
  responsibility: string;
};

export type AgentRow = AgentContent & {
  status: AgentStatus;
  progress: number;
};

export type AgentChatMessage = {
  id: string;
  agentKey: AiWorkspaceAgentKey;
  speaker: string;
  message: string;
  time?: string;
  tone?: "normal" | "active" | "done" | "request" | "handoff" | "thinking" | "explanation" | "human";
  targetAgentKey?: AiWorkspaceAgentKey;
};

export type AgentWorkLog = {
  id: string;
  time: string;
  agentKey: AiWorkspaceAgentKey;
  text: string;
};
