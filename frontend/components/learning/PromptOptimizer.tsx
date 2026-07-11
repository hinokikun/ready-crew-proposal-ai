import { memo } from "react";
import { SimulationPanel } from "@/components/learning/SimulationPanel";
import { statusLabel } from "@/components/learning/LearningAnalyzer";
import type { LearningImprovement } from "@/types/app";

type PromptOptimizerProps = {
  improvements: LearningImprovement[];
  onUpdateStatus: (id: number, status: "adopted" | "rejected") => void;
  updatingId: number | null;
};

function PromptOptimizerBase({ improvements, onUpdateStatus, updatingId }: PromptOptimizerProps) {
  if (!improvements.length) {
    return <p className="learning-empty">プロンプト改善候補はまだありません。Learningを実行してください。</p>;
  }
  return (
    <div className="learning-card-list">
      {improvements.map((item) => (
        <article className="learning-improvement-card" key={item.id}>
          <div className="learning-card-header">
            <div>
              <span>{item.agent} / {item.category}</span>
              <strong>{item.expected_effect}</strong>
            </div>
            <em>{statusLabel(item.status)}</em>
          </div>
          <p>{item.suggested_prompt}</p>
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

export const PromptOptimizer = memo(PromptOptimizerBase);
