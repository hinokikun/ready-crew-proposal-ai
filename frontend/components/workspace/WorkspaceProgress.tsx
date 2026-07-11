"use client";

import { memo } from "react";
import { AiWorkspacePanel, type AiWorkspaceAgentKey } from "@/components/AiWorkspacePanel";

export type { AiWorkspaceAgentKey };

type WorkspaceProgressProps = {
  status: "idle" | "typing" | "analyzing" | "question" | "reviewing" | "generating" | "complete";
  hasInput: boolean;
  hasResult: boolean;
  isLoading: boolean;
  canAdminRerun: boolean;
  canPersist?: boolean;
  canRequestReview?: boolean;
  canCompleteQualityGate?: boolean;
  canBypassQualityGate?: boolean;
  onQualityGateChange?: (unlocked: boolean) => void;
  onRerunAgent: (agent: AiWorkspaceAgentKey) => void;
  workspaceSeed?: string;
  workspaceTitle?: string;
};

function WorkspaceProgressBase(props: WorkspaceProgressProps) {
  return <AiWorkspacePanel {...props} />;
}

export const WorkspaceProgress = memo(WorkspaceProgressBase);
