import type { PromptExperiment, PromptMetricSummary } from "@/types/app";

export function experimentStatusLabel(status: string) {
  const labels: Record<string, string> = {
    draft: "下書き",
    testing: "テスト中",
    active: "実行中",
    paused: "停止中",
    completed: "完了",
    archived: "保管"
  };
  return labels[status] ?? status;
}

export function formatPromptDuration(seconds: number) {
  if (!seconds) return "未計測";
  const minutes = Math.round(seconds / 60);
  return `${minutes}分`;
}

export function findMetricsForExperiment(experiment: PromptExperiment, metrics: PromptMetricSummary[]) {
  return {
    control: metrics.find((item) => item.prompt_name === experiment.target_prompt && item.prompt_version === experiment.control_version),
    candidate: metrics.find((item) => item.prompt_name === experiment.target_prompt && item.prompt_version === experiment.candidate_version)
  };
}
