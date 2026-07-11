import { fetchJson } from "@/client-api/client";
import type { LearningDashboardData, LearningImprovement } from "@/types/app";

export function getLearningDashboard(): Promise<{ dashboard: LearningDashboardData }> {
  return fetchJson("/api/learning/dashboard");
}

export function runLearningAnalysis(): Promise<{ dashboard: LearningDashboardData }> {
  return fetchJson("/api/learning/run", { method: "POST" });
}

export function updateLearningImprovementStatus(
  improvementId: number,
  status: "candidate" | "adopted" | "rejected"
): Promise<{ improvement: LearningImprovement }> {
  return fetchJson(`/api/learning/improvements/${improvementId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status })
  });
}
