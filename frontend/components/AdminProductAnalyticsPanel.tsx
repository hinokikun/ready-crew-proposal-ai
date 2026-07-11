"use client";

import { memo, useEffect, useMemo, useState } from "react";
import {
  createReleaseNote,
  getProductAnalyticsDashboard,
  getReleaseNotes,
  updateProductAnalyticsErrorResolved
} from "@/lib/api";
import { toFriendlyError } from "@/lib/errorMessage";
import type { ProductAnalyticsDashboardData, ReleaseNoteEntry } from "@/types/app";

const emptyDashboard: ProductAnalyticsDashboardData = {
  summary: {
    total_sessions: 0,
    total_events: 0,
    total_errors: 0,
    average_session_seconds: 0
  },
  funnel: [],
  sessions: [],
  errors: [],
  feature_usage: [],
  improvement_candidates: []
};

const funnelLabels: Record<string, string> = {
  login: "ログイン",
  case_paste: "案件貼り付け",
  ai_analysis_start: "AI解析開始",
  ai_analysis_complete: "AI解析完了",
  proposal_generated: "提案書作成",
  summary_ppt_download: "要約PPT",
  detail_ppt_download: "詳細PPT",
  estimate_pdf_download: "見積PDF"
};

function formatDate(value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  return value.replace("T", " ").slice(0, 16);
}

function formatSeconds(value: number) {
  if (value < 60) {
    return `${Math.round(value)}秒`;
  }
  return `${Math.round(value / 60)}分`;
}

function buildAnalyticsMarkdown(dashboard: ProductAnalyticsDashboardData, notes: ReleaseNoteEntry[]) {
  const summary = dashboard.summary;
  return [
    "# Product Analytics Report",
    "",
    "## Summary",
    `- Sessions: ${summary.total_sessions}`,
    `- Events: ${summary.total_events}`,
    `- Errors: ${summary.total_errors}`,
    `- Average Session Time: ${formatSeconds(summary.average_session_seconds)}`,
    "",
    "## Funnel",
    ...dashboard.funnel.map(
      (step) =>
        `- ${funnelLabels[step.step] ?? step.label}: reach ${step.reach_rate}%, drop-off ${step.dropoff_rate}%, avg ${step.average_time_seconds}s`
    ),
    "",
    "## Top Improvements",
    ...dashboard.improvement_candidates.map((item) => `- [${item.priority}] ${item.title}: ${item.next_action}`),
    "",
    "## Release Notes",
    ...notes.slice(0, 5).map((note) => `- ${note.release_date} v${note.version}: ${note.title}`)
  ].join("\n");
}

export const AdminProductAnalyticsPanel = memo(function AdminProductAnalyticsPanel() {
  const [dashboard, setDashboard] = useState<ProductAnalyticsDashboardData>(emptyDashboard);
  const [releaseNotes, setReleaseNotes] = useState<ReleaseNoteEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusMessage, setStatusMessage] = useState("");
  const [newVersion, setNewVersion] = useState("7.0");
  const [newDate, setNewDate] = useState(new Date().toISOString().slice(0, 10));
  const [newTitle, setNewTitle] = useState("Product Analytics");
  const [newImprovements, setNewImprovements] = useState("");

  const markdown = useMemo(() => buildAnalyticsMarkdown(dashboard, releaseNotes), [dashboard, releaseNotes]);

  async function loadAnalytics() {
    setIsLoading(true);
    setStatusMessage("");
    try {
      const [dashboardResponse, releaseResponse] = await Promise.all([
        getProductAnalyticsDashboard(20, 0),
        getReleaseNotes(20, 0)
      ]);
      setDashboard(dashboardResponse.dashboard);
      setReleaseNotes(releaseResponse.release_notes);
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadAnalytics();
  }, []);

  async function toggleResolved(errorId: number, resolved: boolean) {
    try {
      await updateProductAnalyticsErrorResolved(errorId, resolved);
      await loadAnalytics();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  async function saveReleaseNote() {
    if (!newVersion.trim() || !newDate.trim()) {
      setStatusMessage("Versionと日付を入力してください。");
      return;
    }
    try {
      await createReleaseNote({
        version: newVersion,
        release_date: newDate,
        title: newTitle,
        improvements: newImprovements
      });
      setNewImprovements("");
      await loadAnalytics();
      setStatusMessage("リリースノートを保存しました。");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  async function copyMarkdown() {
    await navigator.clipboard.writeText(markdown);
    setStatusMessage("Markdownをコピーしました。");
  }

  if (isLoading) {
    return (
      <section className="admin-usage-dashboard-panel">
        <p className="helper-text">Product Analyticsを読み込んでいます。</p>
      </section>
    );
  }

  return (
    <section className="admin-usage-dashboard-panel">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Version 7.0</p>
          <h3>Product Analytics</h3>
          <p className="helper-text">本文や顧客情報を保存せず、利用状況だけを集計します。</p>
        </div>
        <button className="secondary-button" type="button" onClick={() => void loadAnalytics()}>
          再読み込み
        </button>
      </div>

      {statusMessage ? <p className="status-note">{statusMessage}</p> : null}

      <div className="usage-dashboard-grid">
        <article>
          <span>Session</span>
          <strong>{dashboard.summary.total_sessions}</strong>
          <p>1回の利用単位</p>
        </article>
        <article>
          <span>Event</span>
          <strong>{dashboard.summary.total_events}</strong>
          <p>操作ログ数</p>
        </article>
        <article>
          <span>Error</span>
          <strong>{dashboard.summary.total_errors}</strong>
          <p>失敗イベント数</p>
        </article>
        <article>
          <span>Avg Time</span>
          <strong>{formatSeconds(dashboard.summary.average_session_seconds)}</strong>
          <p>平均利用時間</p>
        </article>
      </div>

      {dashboard.project_lifecycle ? (
        <details className="advanced-foldout" open>
          <summary>Project Lifecycle Analytics</summary>
          <div className="usage-dashboard-grid">
            <article>
              <span>受注率</span>
              <strong>{dashboard.project_lifecycle.win_rate}%</strong>
              <p>受注 {dashboard.project_lifecycle.won_count}件 / 失注 {dashboard.project_lifecycle.lost_count}件</p>
            </article>
            <article>
              <span>平均提案期間</span>
              <strong>{dashboard.project_lifecycle.average_proposal_days}日</strong>
              <p>受付から提出・受注・失注まで</p>
            </article>
            <article>
              <span>レビュー/修正</span>
              <strong>{dashboard.project_lifecycle.review_count} / {dashboard.project_lifecycle.revision_count}</strong>
              <p>レビュー回数 / 修正回数</p>
            </article>
            <article>
              <span>案件完了率</span>
              <strong>{dashboard.project_lifecycle.completion_rate}%</strong>
              <p>完了 {dashboard.project_lifecycle.completed_count}件 / 全体 {dashboard.project_lifecycle.total_projects}件</p>
            </article>
          </div>
        </details>
      ) : null}

      {dashboard.daily_briefing ? (
        <details className="advanced-foldout" open>
          <summary>Daily AI Executive Briefing</summary>
          <div className="usage-dashboard-grid">
            <article>
              <span>朝会表示</span>
              <strong>{dashboard.daily_briefing.views}</strong>
              <p>ログイン後ブリーフィング表示回数</p>
            </article>
            <article>
              <span>優先案件クリック</span>
              <strong>{dashboard.daily_briefing.priority_clicks}</strong>
              <p>おすすめ案件の確認回数</p>
            </article>
            <article>
              <span>完了数</span>
              <strong>{dashboard.daily_briefing.completed}</strong>
              <p>今日の対応を完了にした回数</p>
            </article>
            <article>
              <span>完了率</span>
              <strong>{dashboard.daily_briefing.completion_rate}%</strong>
              <p>クリック後に完了した割合</p>
            </article>
          </div>
        </details>
      ) : null}

      {dashboard.notification_center ? (
        <details className="advanced-foldout" open>
          <summary>AI Notification Center</summary>
          <div className="usage-dashboard-grid">
            <article>
              <span>通知数</span>
              <strong>{dashboard.notification_center.total}</strong>
              <p>AI Watch Engineが生成した通知</p>
            </article>
            <article>
              <span>未読</span>
              <strong>{dashboard.notification_center.unread}</strong>
              <p>未確認の通知</p>
            </article>
            <article>
              <span>既読率</span>
              <strong>{dashboard.notification_center.read_rate}%</strong>
              <p>通知が確認された割合</p>
            </article>
            <article>
              <span>対応率</span>
              <strong>{dashboard.notification_center.action_rate}%</strong>
              <p>対応済みになった割合</p>
            </article>
            <article>
              <span>放置率</span>
              <strong>{dashboard.notification_center.ignored_rate}%</strong>
              <p>3日以上未読の割合</p>
            </article>
          </div>
        </details>
      ) : null}

      {dashboard.integrations ? (
        <details className="advanced-foldout" open>
          <summary>External Workflow Integration</summary>
          <div className="usage-dashboard-grid">
            <article>
              <span>外部入力</span>
              <strong>{dashboard.integrations.external_input_count}</strong>
              <p>メール・予定・チャット・資料から受け取った要約件数</p>
            </article>
            <article>
              <span>案件候補</span>
              <strong>{dashboard.integrations.candidate_count}</strong>
              <p>まだCRM案件化されていない候補</p>
            </article>
            <article>
              <span>案件化済み</span>
              <strong>{dashboard.integrations.converted_count}</strong>
              <p>CRMとAI Workspaceへ引き継いだ件数</p>
            </article>
            <article>
              <span>案件化率</span>
              <strong>{dashboard.integrations.conversion_rate}%</strong>
              <p>外部入力から案件化された割合</p>
            </article>
            <article>
              <span>Dry Run</span>
              <strong>{dashboard.integrations.dry_run_count ?? 0}</strong>
              <p>疑似連携テストの実行回数</p>
            </article>
            <article>
              <span>Readiness</span>
              <strong>{dashboard.integrations.average_readiness_score ?? 0}点</strong>
              <p>Connector Readinessの平均スコア</p>
            </article>
          </div>
          <div className="table-scroll">
            <table className="usage-dashboard-table">
              <thead>
                <tr>
                  <th>Provider</th>
                  <th>件数</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.integrations.provider_counts.map((item) => (
                  <tr key={item.provider}>
                    <td>{item.provider}</td>
                    <td>{item.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {dashboard.integrations.provider_dry_run_success_rates?.length ? (
            <div className="table-scroll">
              <table className="usage-dashboard-table">
                <thead>
                  <tr>
                    <th>Provider</th>
                    <th>Dry Run</th>
                    <th>成功</th>
                    <th>成功率</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard.integrations.provider_dry_run_success_rates.map((item) => (
                    <tr key={item.provider}>
                      <td>{item.provider}</td>
                      <td>{item.total}</td>
                      <td>{item.success_count}</td>
                      <td>{item.success_rate}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </details>
      ) : null}

      {dashboard.orchestrator ? (
        <details className="advanced-foldout" open>
          <summary>Autonomous Project Orchestrator</summary>
          <div className="usage-dashboard-grid">
            <article>
              <span>Action</span>
              <strong>{dashboard.orchestrator.total_actions}</strong>
              <p>AI社員が処理したキュー数</p>
            </article>
            <article>
              <span>Avg Process</span>
              <strong>{formatSeconds(dashboard.orchestrator.average_processing_seconds)}</strong>
              <p>平均処理時間</p>
            </article>
            <article>
              <span>Retry</span>
              <strong>{dashboard.orchestrator.retry_rate}%</strong>
              <p>リトライが発生した割合</p>
            </article>
            <article>
              <span>Autonomous</span>
              <strong>{dashboard.orchestrator.autonomous_completion_rate}%</strong>
              <p>人間介入なしで完了した案件割合</p>
            </article>
            <article>
              <span>Human</span>
              <strong>{dashboard.orchestrator.human_intervention_rate}%</strong>
              <p>人間確認で停止した割合</p>
            </article>
          </div>
          {dashboard.orchestrator.agent_times.length ? (
            <div className="table-scroll">
              <table className="usage-dashboard-table">
                <thead>
                  <tr>
                    <th>AI社員</th>
                    <th>担当数</th>
                    <th>平均</th>
                    <th>合計</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard.orchestrator.agent_times.map((item) => (
                    <tr key={item.agent}>
                      <td>{item.agent}</td>
                      <td>{item.action_count}</td>
                      <td>{formatSeconds(item.average_seconds)}</td>
                      <td>{formatSeconds(item.total_seconds)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </details>
      ) : null}

      {dashboard.learning ? (
        <details className="advanced-foldout" open>
          <summary>AI Learning & Optimization</summary>
          <div className="usage-dashboard-grid">
            <article>
              <span>Learning</span>
              <strong>{dashboard.learning.learning_runs}</strong>
              <p>Learning実行回数</p>
            </article>
            <article>
              <span>Adoption</span>
              <strong>{dashboard.learning.improvement_adoption_rate}%</strong>
              <p>改善採用率</p>
            </article>
            <article>
              <span>Win Effect</span>
              <strong>+{dashboard.learning.average_expected_win_rate_delta}%</strong>
              <p>平均期待改善率</p>
            </article>
            <article>
              <span>Prompt</span>
              <strong>{dashboard.learning.prompt_improvements}</strong>
              <p>Prompt改善数</p>
            </article>
            <article>
              <span>Workflow</span>
              <strong>{dashboard.learning.workflow_improvements}</strong>
              <p>Workflow改善数</p>
            </article>
          </div>
        </details>
      ) : null}

      {dashboard.prompt_experiments ? (
        <details className="advanced-foldout" open>
          <summary>Prompt Experiments</summary>
          <div className="usage-dashboard-grid">
            <article>
              <span>Versions</span>
              <strong>{dashboard.prompt_experiments.prompt_versions_count}</strong>
              <p>Prompt Version数</p>
            </article>
            <article>
              <span>Experiments</span>
              <strong>{dashboard.prompt_experiments.experiments_count}</strong>
              <p>A/Bテスト数</p>
            </article>
            <article>
              <span>Active</span>
              <strong>{dashboard.prompt_experiments.active_experiments_count}</strong>
              <p>実行中テスト</p>
            </article>
            <article>
              <span>Assignments</span>
              <strong>{dashboard.prompt_experiments.assignments_count}</strong>
              <p>Prompt割当</p>
            </article>
            <article>
              <span>Metrics</span>
              <strong>{dashboard.prompt_experiments.metrics_count}</strong>
              <p>効果測定件数</p>
            </article>
          </div>
          {dashboard.prompt_experiments.winner_recommendations.length ? (
            <div className="prompt-recommendation-list">
              {dashboard.prompt_experiments.winner_recommendations.slice(0, 3).map((item) => (
                <article className="prompt-recommendation-card" key={`${item.experiment_id}-${item.recommended_version || "pending"}`}>
                  <span>{item.target_prompt}</span>
                  <strong>{item.recommended_version || "判定待ち"}</strong>
                  <p>{item.reason}</p>
                </article>
              ))}
            </div>
          ) : null}
        </details>
      ) : null}

      <details className="advanced-foldout" open>
        <summary>Funnel Analytics</summary>
        <div className="table-scroll">
          <table className="usage-dashboard-table">
            <thead>
              <tr>
                <th>ステップ</th>
                <th>到達数</th>
                <th>到達率</th>
                <th>離脱率</th>
                <th>平均時間</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.funnel.map((step) => (
                <tr key={step.step}>
                  <td>{funnelLabels[step.step] ?? step.label}</td>
                  <td>{step.sessions}</td>
                  <td>{step.reach_rate}%</td>
                  <td>{step.dropoff_rate}%</td>
                  <td>{step.average_time_seconds}秒</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>

      <details className="advanced-foldout">
        <summary>Session分析</summary>
        <div className="table-scroll">
          <table className="usage-dashboard-table">
            <thead>
              <tr>
                <th>開始</th>
                <th>ロール</th>
                <th>利用時間</th>
                <th>作成</th>
                <th>DL</th>
                <th>エラー</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.sessions.map((session) => (
                <tr key={session.id}>
                  <td>{formatDate(session.started_at)}</td>
                  <td>{session.user_role}</td>
                  <td>{formatSeconds(session.duration_seconds)}</td>
                  <td>{session.generation_count}</td>
                  <td>{session.download_count}</td>
                  <td>{session.error_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>

      <details className="advanced-foldout">
        <summary>エラーTOP10</summary>
        <div className="table-scroll">
          <table className="usage-dashboard-table">
            <thead>
              <tr>
                <th>カテゴリ</th>
                <th>発生源</th>
                <th>件数</th>
                <th>割合</th>
                <th>最終発生日</th>
                <th>状態</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.errors.map((error) => (
                <tr key={error.id}>
                  <td>{error.category}</td>
                  <td>{error.source}</td>
                  <td>{error.count}</td>
                  <td>{error.percentage}%</td>
                  <td>{formatDate(error.last_seen_at)}</td>
                  <td>
                    <button className="secondary-button compact-button" type="button" onClick={() => void toggleResolved(error.id, !error.resolved)}>
                      {error.resolved ? "改善済み" : "未改善"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>

      <details className="advanced-foldout">
        <summary>Feature Usage</summary>
        <div className="table-scroll">
          <table className="usage-dashboard-table">
            <thead>
              <tr>
                <th>機能</th>
                <th>イベント</th>
                <th>Session</th>
                <th>利用率</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.feature_usage.map((feature) => (
                <tr key={feature.feature_key}>
                  <td>{feature.feature_name}</td>
                  <td>{feature.event_count}</td>
                  <td>{feature.session_count}</td>
                  <td>{feature.usage_rate}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>

      <details className="advanced-foldout" open>
        <summary>AI改善候補</summary>
        <div className="insight-list">
          {dashboard.improvement_candidates.map((item) => (
            <article className="insight-card" key={`${item.priority}-${item.title}`}>
              <span>{item.priority}</span>
              <strong>{item.title}</strong>
              <p>{item.reason}</p>
              <p>{item.hypothesis}</p>
              <small>{item.next_action}</small>
            </article>
          ))}
        </div>
      </details>

      <details className="advanced-foldout">
        <summary>Release Notes</summary>
        <div className="release-note-form">
          <label className="field">
            <span>Version</span>
            <input value={newVersion} onChange={(event) => setNewVersion(event.target.value)} />
          </label>
          <label className="field">
            <span>日付</span>
            <input type="date" value={newDate} onChange={(event) => setNewDate(event.target.value)} />
          </label>
          <label className="field">
            <span>今回の改善</span>
            <input value={newTitle} onChange={(event) => setNewTitle(event.target.value)} />
          </label>
          <label className="field">
            <span>詳細</span>
            <textarea rows={4} value={newImprovements} onChange={(event) => setNewImprovements(event.target.value)} />
          </label>
          <div className="button-row">
            <button className="primary-button" type="button" onClick={() => void saveReleaseNote()}>
              保存
            </button>
            <button className="secondary-button" type="button" onClick={() => void copyMarkdown()}>
              Markdownをコピー
            </button>
          </div>
        </div>
        <div className="insight-list">
          {releaseNotes.map((note) => (
            <article className="insight-card" key={note.id}>
              <span>{note.release_date}</span>
              <strong>v{note.version} {note.title}</strong>
              <p>{note.improvements}</p>
              <small>{note.created_by_email || "admin"}</small>
            </article>
          ))}
        </div>
      </details>
    </section>
  );
});
