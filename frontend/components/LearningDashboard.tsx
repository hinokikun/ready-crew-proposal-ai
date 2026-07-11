"use client";

import { memo, useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { sortLearningImprovements } from "@/components/learning/LearningAnalyzer";
import { PromptOptimizer } from "@/components/learning/PromptOptimizer";
import { WorkflowOptimizer } from "@/components/learning/WorkflowOptimizer";
import { getLearningDashboard, runLearningAnalysis, updateLearningImprovementStatus } from "@/lib/api";
import type { LearningDashboardData } from "@/types/app";

function emptyDashboard(): LearningDashboardData {
  return {
    run: null,
    improvements: [],
    release_candidate: {
      version: "未作成",
      summary: "Learningを実行すると、次回改善候補とリリース候補が表示されます。"
    },
    analytics: {
      learning_runs: 0,
      improvement_adoption_rate: 0,
      average_expected_win_rate_delta: 0,
      prompt_improvements: 0,
      workflow_improvements: 0,
      total_improvements: 0
    }
  };
}

function normalizeDashboard(dashboard?: Partial<LearningDashboardData> | null): LearningDashboardData {
  const fallback = emptyDashboard();
  return {
    run: dashboard?.run ?? fallback.run,
    improvements: Array.isArray(dashboard?.improvements) ? dashboard.improvements : [],
    release_candidate: {
      version: dashboard?.release_candidate?.version ?? fallback.release_candidate.version,
      summary: dashboard?.release_candidate?.summary ?? fallback.release_candidate.summary
    },
    analytics: {
      learning_runs: dashboard?.analytics?.learning_runs ?? 0,
      improvement_adoption_rate: dashboard?.analytics?.improvement_adoption_rate ?? 0,
      average_expected_win_rate_delta: dashboard?.analytics?.average_expected_win_rate_delta ?? 0,
      prompt_improvements: dashboard?.analytics?.prompt_improvements ?? 0,
      workflow_improvements: dashboard?.analytics?.workflow_improvements ?? 0,
      total_improvements: dashboard?.analytics?.total_improvements ?? 0
    }
  };
}

function LearningDashboardBase() {
  const [dashboard, setDashboard] = useState<LearningDashboardData>(() => emptyDashboard());
  const [isLoading, setIsLoading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [notice, setNotice] = useState("");

  const sortedImprovements = useMemo(() => sortLearningImprovements(dashboard.improvements), [dashboard.improvements]);
  const promptImprovements = useMemo(
    () => sortedImprovements.filter((item) => item.improvement_type === "prompt"),
    [sortedImprovements]
  );
  const workflowImprovements = useMemo(
    () => sortedImprovements.filter((item) => item.improvement_type !== "prompt"),
    [sortedImprovements]
  );

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setNotice("");
    try {
      const response = await getLearningDashboard();
      setDashboard(normalizeDashboard(response.dashboard));
    } catch {
      setDashboard(emptyDashboard());
      setNotice("AI Learning Dashboardを読み込めませんでした。Backend接続と権限を確認してください。");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const runLearning = useCallback(async () => {
    setIsRunning(true);
    setNotice("");
    try {
      const response = await runLearningAnalysis();
      setDashboard(normalizeDashboard(response.dashboard));
      setNotice("Learningを実行し、改善候補を更新しました。");
    } catch {
      setNotice("Learning実行に失敗しました。BackendログとDB接続を確認してください。");
    } finally {
      setIsRunning(false);
    }
  }, []);

  const updateStatus = useCallback(
    async (id: number, status: "adopted" | "rejected") => {
      setUpdatingId(id);
      setNotice("");
      try {
        await updateLearningImprovementStatus(id, status);
        await loadDashboard();
        setNotice(status === "adopted" ? "改善候補を採用にしました。" : "改善候補を見送りにしました。");
      } catch {
        setNotice("改善候補の状態更新に失敗しました。権限を確認してください。");
      } finally {
        setUpdatingId(null);
      }
    },
    [loadDashboard]
  );

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  return (
    <section className="learning-dashboard-panel">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Version 13.5</p>
          <h3>AI Learning Dashboard</h3>
          <p className="helper-text">レビュー、受注率、Quality Gate、Knowledge、通知、Workspaceログを匿名集計し、改善候補を表示します。</p>
        </div>
        <button className="primary-button" type="button" onClick={() => void runLearning()} disabled={isRunning}>
          {isRunning ? <Loader2 className="spin" size={16} aria-hidden="true" /> : <Sparkles size={16} aria-hidden="true" />}
          Learningを実行
        </button>
      </div>

      {notice ? <p className="status-note">{notice}</p> : null}
      {isLoading ? <p className="learning-empty">Learning Dashboardを読み込み中です。</p> : null}

      <div className="learning-summary-grid">
        <article><span>Learning実行</span><strong>{dashboard.analytics.learning_runs}</strong></article>
        <article><span>改善採用率</span><strong>{dashboard.analytics.improvement_adoption_rate}%</strong></article>
        <article><span>期待受注率改善</span><strong>+{dashboard.analytics.average_expected_win_rate_delta}%</strong></article>
        <article><span>Prompt改善</span><strong>{dashboard.analytics.prompt_improvements}</strong></article>
        <article><span>Workflow改善</span><strong>{dashboard.analytics.workflow_improvements}</strong></article>
      </div>

      <section className="learning-release-candidate">
        <div>
          <span>Release候補</span>
          <strong>{dashboard.release_candidate.version}</strong>
        </div>
        <pre>{dashboard.release_candidate.summary}</pre>
      </section>

      <details className="advanced-foldout" open>
        <summary>Prompt Improvement</summary>
        <PromptOptimizer improvements={promptImprovements} onUpdateStatus={updateStatus} updatingId={updatingId} />
      </details>

      <details className="advanced-foldout" open>
        <summary>Workflow / Rule Optimization</summary>
        <WorkflowOptimizer improvements={workflowImprovements} onUpdateStatus={updateStatus} updatingId={updatingId} />
      </details>
    </section>
  );
}

export const LearningDashboard = memo(LearningDashboardBase);
