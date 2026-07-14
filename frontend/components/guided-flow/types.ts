import type { ReactNode } from "react";

export type GuidedStepId = 1 | 2 | 3 | 4 | 5 | 6 | 7;

export type GuidedStep = {
  id: GuidedStepId;
  shortLabel: string;
  title: string;
};

export type GuidedSummaryItem = {
  label: string;
  value: string;
  inferred?: boolean;
};

export type GuidedProgressStatus = "waiting" | "running" | "done" | "error";

export type GuidedProgressStage = {
  label: string;
  status: GuidedProgressStatus;
  helper?: string;
};

export type GuidedQualityGate = {
  completed?: boolean;
  bypassed?: boolean;
  download_unlocked?: boolean;
  completed_at?: string | null;
  updated_at?: string | null;
  user_id?: number | null;
};

export type BeautifulAiSimpleRequirement = {
  label: string;
  passed: boolean;
  reason: string;
};

export type GuidedFlowPanels = {
  workspaceProgress: ReactNode;
  presentationReview: ReactNode;
  proposalOptimization: ReactNode;
  beautifulAiDiagnostics: ReactNode;
};
