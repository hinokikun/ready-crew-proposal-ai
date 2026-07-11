import { memo } from "react";
import { learningTypeLabel, statusLabel } from "@/components/learning/LearningAnalyzer";
import { SimulationPanel } from "@/components/learning/SimulationPanel";
import type { LearningImprovement } from "@/types/app";

type WorkflowOptimizerProps = {
  improvements: LearningImprovement[];
  onUpdateStatus: (id: number, status: "adopted" | "rejected") => void;
  updatingId: number | null;
};

function WorkflowOptimizerBase({ improvements, onUpdateStatus, updatingId }: WorkflowOptimizerProps) {
  if (!improvements.length) {
    return <p className="learning-empty">ワークフロー改善候補はまだありません。</p>;
  }
  return (
    <div className="learning-card-list">
      {improvements.map((item) => (
        <article className="learning-improvement-card" key={item.id}>
          <div className="learning-card-header">
            <div>
              <span>{learningTypeLabel(item.improvement_type)} / {item.agent}</span>
              <strong>{item.category}</strong>
            </div>
            <em>{statusLabel(item.status)}</em>
          </div>
          <p>{item.recommendation}</p>
          <p className="learning-effect">{item.expected_effect}</p>
          <SimulationPanel simulation={item.simulation} />
          <div className="learning-card-meta">
            <span>信頼度 {item.confidence}%</span>
            <span>推奨順位 {item.priority}</span>
            <span>{item.current_version}</span>
          </div>
          <div className="learning-card-actions">
            <button className="secondary-button" type="button" onClick={() => onUpdateStatus(item.id, "adopted")} disabled={updatingId === item.id}>
              採用
            </button>
            <button className="secondary-button" type="button" onClick={() => onUpdateStatus(item.id, "rejected")} disabled={updatingId === item.id}>
              見送り
            </button>
          </div>
        </article>
      ))}
    </div>
  );
}

export const WorkflowOptimizer = memo(WorkflowOptimizerBase);
