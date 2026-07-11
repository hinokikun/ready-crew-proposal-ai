"use client";

import { memo, useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { ExperimentDashboard } from "@/components/prompts/ExperimentDashboard";
import { PromptHistory } from "@/components/prompts/PromptHistory";
import {
  createPromptExperiment,
  createPromptExperimentFromLearning,
  createPromptVersion,
  getLearningDashboard,
  getPromptStudioDashboard,
  judgePromptExperiment,
  rollbackPromptVersion,
  updatePromptVersionStatus,
  type PromptExperimentPayload,
  type PromptVersionPayload
} from "@/lib/api";
import type { LearningDashboardData, PromptStudioDashboardData } from "@/types/app";

function emptyPromptDashboard(): PromptStudioDashboardData {
  return {
    versions: [],
    experiments: [],
    analytics: {
      prompt_versions_count: 0,
      experiments_count: 0,
      active_experiments_count: 0,
      assignments_count: 0,
      metrics_count: 0,
      prompt_metrics: [],
      winner_recommendations: []
    },
    winner_recommendations: []
  };
}

type PromptDashboardInput = Partial<Omit<PromptStudioDashboardData, "analytics">> & {
  analytics?: Partial<PromptStudioDashboardData["analytics"]>;
};

function normalizePromptDashboard(dashboard?: PromptDashboardInput | null): PromptStudioDashboardData {
  const fallback = emptyPromptDashboard();
  return {
    versions: Array.isArray(dashboard?.versions) ? dashboard.versions : [],
    experiments: Array.isArray(dashboard?.experiments) ? dashboard.experiments : [],
    analytics: {
      prompt_versions_count: dashboard?.analytics?.prompt_versions_count ?? 0,
      experiments_count: dashboard?.analytics?.experiments_count ?? 0,
      active_experiments_count: dashboard?.analytics?.active_experiments_count ?? 0,
      assignments_count: dashboard?.analytics?.assignments_count ?? 0,
      metrics_count: dashboard?.analytics?.metrics_count ?? 0,
      prompt_metrics: Array.isArray(dashboard?.analytics?.prompt_metrics) ? dashboard.analytics.prompt_metrics : [],
      winner_recommendations: Array.isArray(dashboard?.analytics?.winner_recommendations)
        ? dashboard.analytics.winner_recommendations
        : []
    },
    winner_recommendations: Array.isArray(dashboard?.winner_recommendations)
      ? dashboard.winner_recommendations
      : fallback.winner_recommendations
  };
}

function emptyVersionPayload(): PromptVersionPayload {
  return {
    prompt_name: "proposal_generation",
    version: "v1",
    description: "営業提案書生成の基準Prompt",
    target_agent: "AI営業",
    prompt_template: "案件概要から、顧客課題・提案方針・次アクションを営業提案向けに整理してください。",
    status: "draft"
  };
}

function emptyExperimentPayload(): PromptExperimentPayload {
  return {
    experiment_name: "proposal_generation v1/v2 test",
    target_prompt: "proposal_generation",
    control_version: "v1",
    candidate_version: "v2",
    traffic_ratio: 50,
    status: "testing",
    start_at: "",
    end_at: ""
  };
}

function PromptStudioBase() {
  const [dashboard, setDashboard] = useState<PromptStudioDashboardData>(() => emptyPromptDashboard());
  const [learningDashboard, setLearningDashboard] = useState<LearningDashboardData | null>(null);
  const [versionForm, setVersionForm] = useState<PromptVersionPayload>(() => emptyVersionPayload());
  const [experimentForm, setExperimentForm] = useState<PromptExperimentPayload>(() => emptyExperimentPayload());
  const [notice, setNotice] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSavingVersion, setIsSavingVersion] = useState(false);
  const [isSavingExperiment, setIsSavingExperiment] = useState(false);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [judgingId, setJudgingId] = useState<number | null>(null);
  const [learningId, setLearningId] = useState<number | null>(null);

  const promptImprovements = useMemo(
    () => (learningDashboard?.improvements ?? []).filter((item) => item.improvement_type === "prompt").slice(0, 5),
    [learningDashboard]
  );

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setNotice("");
    try {
      const [promptResponse, learningResponse] = await Promise.all([
        getPromptStudioDashboard(),
        getLearningDashboard().catch(() => null)
      ]);
      setDashboard(normalizePromptDashboard(promptResponse.dashboard));
      if (learningResponse) {
        setLearningDashboard(learningResponse.dashboard);
      }
    } catch {
      setNotice("Prompt Studioを読み込めませんでした。Backend接続と権限を確認してください。");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const saveVersion = useCallback(async () => {
    setIsSavingVersion(true);
    setNotice("");
    try {
      const response = await createPromptVersion(versionForm);
      setDashboard(normalizePromptDashboard(response.dashboard));
      setVersionForm((current) => ({ ...current, version: nextVersionLabel(current.version) }));
      setNotice("Prompt Versionを保存しました。");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Prompt Versionの保存に失敗しました。");
    } finally {
      setIsSavingVersion(false);
    }
  }, [versionForm]);

  const saveExperiment = useCallback(async () => {
    setIsSavingExperiment(true);
    setNotice("");
    try {
      const response = await createPromptExperiment(experimentForm);
      setDashboard(normalizePromptDashboard(response.dashboard));
      setNotice("A/Bテストを作成しました。");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "A/Bテストの作成に失敗しました。");
    } finally {
      setIsSavingExperiment(false);
    }
  }, [experimentForm]);

  const setPromptStatus = useCallback(async (versionId: number, status: "draft" | "testing" | "active" | "archived") => {
    setUpdatingId(versionId);
    setNotice("");
    try {
      const response = await updatePromptVersionStatus(versionId, status);
      setDashboard(normalizePromptDashboard(response.dashboard));
      setNotice("Prompt Versionの状態を更新しました。");
    } catch {
      setNotice("Prompt Versionの状態更新に失敗しました。");
    } finally {
      setUpdatingId(null);
    }
  }, []);

  const rollbackVersion = useCallback(async (promptName: string, version: string) => {
    setNotice("");
    try {
      const response = await rollbackPromptVersion(promptName, version);
      setDashboard(normalizePromptDashboard(response.dashboard));
      setNotice(`${promptName} を ${version} に戻しました。`);
    } catch {
      setNotice("Rollbackに失敗しました。対象Versionを確認してください。");
    }
  }, []);

  const judgeExperiment = useCallback(async (experimentId: number) => {
    setJudgingId(experimentId);
    setNotice("");
    try {
      const response = await judgePromptExperiment(experimentId);
      setDashboard(normalizePromptDashboard(response.dashboard));
      setNotice(response.recommendation.recommended_version ? `Winner候補: ${response.recommendation.recommended_version}` : response.recommendation.reason);
    } catch {
      setNotice("Winner判定には、Control/Candidateそれぞれの測定データがもう少し必要です。");
    } finally {
      setJudgingId(null);
    }
  }, []);

  const createFromLearning = useCallback(async (improvementId: number) => {
    setLearningId(improvementId);
    setNotice("");
    try {
      const response = await createPromptExperimentFromLearning(improvementId);
      setDashboard(normalizePromptDashboard(response.dashboard));
      setNotice("Learning候補からPrompt VersionとA/Bテストを作成しました。");
    } catch {
      setNotice("Learning候補のPrompt化に失敗しました。候補が存在するか確認してください。");
    } finally {
      setLearningId(null);
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  return (
    <section className="prompt-studio-panel">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Version 14.0</p>
          <h3>Prompt Studio</h3>
          <p className="helper-text">Prompt Version、A/Bテスト、効果測定、Winner判定、Rollbackを管理します。</p>
        </div>
        <button className="secondary-button" type="button" onClick={() => void loadDashboard()} disabled={isLoading}>
          {isLoading ? <Loader2 className="spin" size={16} aria-hidden="true" /> : <Sparkles size={16} aria-hidden="true" />}
          再読み込み
        </button>
      </div>

      {notice && <p className="status-note">{notice}</p>}

      <details className="advanced-foldout" open>
        <summary>Prompt Versionを作成</summary>
        <div className="prompt-form-grid">
          <label className="field">
            <span>Prompt名</span>
            <input value={versionForm.prompt_name} onChange={(event) => setVersionForm({ ...versionForm, prompt_name: event.target.value })} />
          </label>
          <label className="field">
            <span>Version</span>
            <input value={versionForm.version} onChange={(event) => setVersionForm({ ...versionForm, version: event.target.value })} />
          </label>
          <label className="field">
            <span>対象AI社員</span>
            <input value={versionForm.target_agent} onChange={(event) => setVersionForm({ ...versionForm, target_agent: event.target.value })} />
          </label>
          <label className="field">
            <span>状態</span>
            <select value={versionForm.status} onChange={(event) => setVersionForm({ ...versionForm, status: event.target.value as PromptVersionPayload["status"] })}>
              <option value="draft">下書き</option>
              <option value="testing">テスト中</option>
              <option value="active">有効</option>
              <option value="archived">保管</option>
            </select>
          </label>
          <label className="field wide-field">
            <span>説明</span>
            <input value={versionForm.description} onChange={(event) => setVersionForm({ ...versionForm, description: event.target.value })} />
          </label>
          <label className="field wide-field">
            <span>Prompt本文</span>
            <textarea rows={5} value={versionForm.prompt_template} onChange={(event) => setVersionForm({ ...versionForm, prompt_template: event.target.value })} />
          </label>
        </div>
        <button className="primary-button" type="button" onClick={() => void saveVersion()} disabled={isSavingVersion}>
          {isSavingVersion ? "保存中" : "Prompt Versionを保存"}
        </button>
      </details>

      <details className="advanced-foldout" open>
        <summary>Learning候補からExperiment作成</summary>
        <div className="learning-card-list">
          {promptImprovements.map((item) => (
            <article className="learning-improvement-card" key={item.id}>
              <div className="learning-card-header">
                <div>
                  <span>{item.agent}</span>
                  <strong>{item.category || "Prompt改善"}</strong>
                </div>
                <small>信頼度 {item.confidence}%</small>
              </div>
              <p>{item.expected_effect}</p>
              <button className="secondary-button" type="button" onClick={() => void createFromLearning(item.id)} disabled={learningId === item.id}>
                {learningId === item.id ? "作成中" : "Prompt化してA/Bテスト作成"}
              </button>
            </article>
          ))}
          {!promptImprovements.length ? <p className="learning-empty">Prompt改善候補がありません。先にAI Learningを実行してください。</p> : null}
        </div>
      </details>

      <details className="advanced-foldout" open>
        <summary>A/Bテストを作成</summary>
        <div className="prompt-form-grid">
          <label className="field wide-field">
            <span>Experiment名</span>
            <input value={experimentForm.experiment_name} onChange={(event) => setExperimentForm({ ...experimentForm, experiment_name: event.target.value })} />
          </label>
          <label className="field">
            <span>対象Prompt</span>
            <input value={experimentForm.target_prompt} onChange={(event) => setExperimentForm({ ...experimentForm, target_prompt: event.target.value })} />
          </label>
          <label className="field">
            <span>Control</span>
            <input value={experimentForm.control_version} onChange={(event) => setExperimentForm({ ...experimentForm, control_version: event.target.value })} />
          </label>
          <label className="field">
            <span>Candidate</span>
            <input value={experimentForm.candidate_version} onChange={(event) => setExperimentForm({ ...experimentForm, candidate_version: event.target.value })} />
          </label>
          <label className="field">
            <span>Candidate配分</span>
            <input
              type="number"
              min={0}
              max={100}
              value={experimentForm.traffic_ratio}
              onChange={(event) => setExperimentForm({ ...experimentForm, traffic_ratio: Number(event.target.value) })}
            />
          </label>
        </div>
        <button className="primary-button" type="button" onClick={() => void saveExperiment()} disabled={isSavingExperiment}>
          {isSavingExperiment ? "作成中" : "A/Bテストを作成"}
        </button>
      </details>

      <details className="advanced-foldout" open>
        <summary>Version履歴 / Rollback</summary>
        <PromptHistory versions={dashboard.versions} updatingId={updatingId} onSetStatus={setPromptStatus} onRollback={rollbackVersion} />
      </details>

      <details className="advanced-foldout" open>
        <summary>A/Bテスト / Winner判定</summary>
        <ExperimentDashboard
          experiments={dashboard.experiments}
          analytics={dashboard.analytics}
          recommendations={dashboard.winner_recommendations}
          judgingId={judgingId}
          onJudge={judgeExperiment}
        />
      </details>
    </section>
  );
}

function nextVersionLabel(version: string) {
  const match = version.match(/^(.*?)(\d+)$/);
  if (!match) return version;
  return `${match[1]}${Number(match[2]) + 1}`;
}

export const PromptStudio = memo(PromptStudioBase);
