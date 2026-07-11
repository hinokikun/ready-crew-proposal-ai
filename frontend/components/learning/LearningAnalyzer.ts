import type { LearningImprovement } from "@/types/app";

export function sortLearningImprovements(items: LearningImprovement[]) {
  return [...items].sort((a, b) => {
    const priorityDiff = b.priority - a.priority;
    if (priorityDiff !== 0) return priorityDiff;
    return b.confidence - a.confidence;
  });
}

export function learningTypeLabel(type: string) {
  if (type === "prompt") return "Prompt改善";
  if (type === "workflow") return "Workflow改善";
  if (type === "rule") return "Rule改善";
  return type;
}

export function statusLabel(status: string) {
  if (status === "adopted") return "採用";
  if (status === "rejected") return "見送り";
  return "候補";
}
