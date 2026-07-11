import { memo } from "react";
import type { LearningSimulation } from "@/types/app";

type SimulationPanelProps = {
  simulation: LearningSimulation;
};

function formatDelta(value: number | undefined, suffix = "%") {
  if (value === undefined || Number.isNaN(value)) return "±0";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value}${suffix}`;
}

function SimulationPanelBase({ simulation }: SimulationPanelProps) {
  return (
    <div className="learning-simulation-grid" aria-label="改善シミュレーション">
      <span>受注率 {formatDelta(simulation.win_rate_delta)}</span>
      <span>レビュー回数 {formatDelta(simulation.review_count_delta, "")}</span>
      <span>品質ゲート {formatDelta(simulation.quality_gate_pass_delta)}</span>
      <span>提案時間 {formatDelta(simulation.proposal_time_delta, "分")}</span>
    </div>
  );
}

export const SimulationPanel = memo(SimulationPanelBase);
