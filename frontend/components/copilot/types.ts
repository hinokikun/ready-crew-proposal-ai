import type { OperationsDashboardInput } from "@/components/dashboard/types";

export type CopilotRecommendation = {
  id: string;
  stars: string;
  title: string;
  detail: string;
  actionLabel: string;
  targetPanelId: string;
  confidence: number;
  reasons: string[];
  signals: string[];
};

export type CopilotTodoItem = {
  id: string;
  label: string;
  targetPanelId: string;
};

export type CopilotChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
};

export type CopilotModel = {
  headline: string;
  reasons: string[];
  recommendation: string;
  recommendations: CopilotRecommendation[];
  todos: CopilotTodoItem[];
  commandMap: Record<string, string>;
};

export type SalesCopilotInput = OperationsDashboardInput & {
  isAdmin: boolean;
  onOpenPanel: (panelId: string) => void;
};
