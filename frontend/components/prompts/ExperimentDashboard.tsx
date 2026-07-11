"use client";

import { memo } from "react";
import type { PromptExperiment, PromptExperimentAnalytics, PromptWinnerRecommendation } from "@/types/app";
import { experimentStatusLabel, findMetricsForExperiment, formatPromptDuration } from "@/components/prompts/ExperimentService";

type ExperimentDashboardProps = {
  experiments: PromptExperiment[];
  analytics: PromptExperimentAnalytics;
  recommendations: PromptWinnerRecommendation[];
  judgingId: number | null;
  onJudge: (experimentId: number) => void;
};

export const ExperimentDashboard = memo(function ExperimentDashboard({
  experiments,
  analytics,
  recommendations,
  judgingId,
  onJudge
}: ExperimentDashboardProps) {
  return (
    <div className="experiment-dashboard">
      <div className="learning-summary-grid">
        <article><span>Prompt Version</span><strong>{analytics.prompt_versions_count}</strong></article>
        <article><span>A/Bテスト</span><strong>{analytics.experiments_count}</strong></article>
        <article><span>実行中</span><strong>{analytics.active_experiments_count}</strong></article>
        <article><span>割当</span><strong>{analytics.assignments_count}</strong></article>
        <article><span>測定</span><strong>{analytics.metrics_count}</strong></article>
      </div>

      {recommendations.length ? (
        <div className="prompt-recommendation-list">
          {recommendations.map((item) => (
            <article className="prompt-recommendation-card" key={`${item.experiment_id}-${item.recommended_version || "pending"}`}>
              <span>Winner候補</span>
              <strong>{item.recommended_version || "判定待ち"}</strong>
              <p>{item.reason}</p>
              <small>信頼度 {item.confidence}% / {item.experiment_name}</small>
            </article>
          ))}
        </div>
      ) : null}

      <div className="table-scroll">
        <table className="usage-dashboard-table">
          <thead>
            <tr>
              <th>Experiment</th>
              <th>対象Prompt</th>
              <th>Control</th>
              <th>Candidate</th>
              <th>配分</th>
              <th>状態</th>
              <th>Winner</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {experiments.map((experiment) => {
              const metrics = findMetricsForExperiment(experiment, analytics.prompt_metrics);
              return (
                <tr key={experiment.id}>
                  <td>
                    <strong>{experiment.experiment_name}</strong>
                    <small className="table-subtext">候補平均 {formatPromptDuration(metrics.candidate?.average_proposal_time_seconds ?? 0)}</small>
                  </td>
                  <td>{experiment.target_prompt}</td>
                  <td>{experiment.control_version}<small className="table-subtext">勝率 {metrics.control?.win_rate ?? 0}%</small></td>
                  <td>{experiment.candidate_version}<small className="table-subtext">勝率 {metrics.candidate?.win_rate ?? 0}%</small></td>
                  <td>{experiment.traffic_ratio}%</td>
                  <td>{experimentStatusLabel(experiment.status)}</td>
                  <td>{experiment.winner || "未判定"}</td>
                  <td>
                    <button
                      className="secondary-button compact-action"
                      type="button"
                      onClick={() => onJudge(experiment.id)}
                      disabled={judgingId === experiment.id}
                    >
                      判定
                    </button>
                  </td>
                </tr>
              );
            })}
            {!experiments.length ? (
              <tr>
                <td colSpan={8}>A/Bテストはまだ作成されていません。</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
});
