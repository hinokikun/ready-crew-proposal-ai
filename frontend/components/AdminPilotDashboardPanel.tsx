"use client";

import { useEffect, useMemo, useState } from "react";
import {
  applyPilotDataRetention,
  createPilotIssue,
  createPilotIssueFromFeedback,
  endPilot,
  getPilotDashboard,
  type PilotDashboardData,
  type PilotEndReport,
  type PilotIssue,
  type PilotIssueStatus,
  updatePilotIssue,
  updatePilotMaintenance
} from "@/lib/api";
import { toFriendlyError } from "@/lib/errorMessage";

const ISSUE_CATEGORIES = ["操作方法", "UI表示", "AI出力", "PPT/PDF", "認証", "権限", "Backend", "DB", "その他"];
const ISSUE_SEVERITIES = ["critical", "high", "medium", "low"] as const;
const ISSUE_STATUSES = ["reported", "investigating", "fixing", "resolved", "deferred"] as const;

const RETENTION_ACTIONS = [
  { value: "keep_summary_only", label: "集計データのみ保持" },
  { value: "anonymize_events", label: "Pilotイベントを匿名化して保持" },
  { value: "delete_events", label: "Pilotイベントを削除" },
  { value: "anonymize_feedback", label: "Pilotフィードバックを匿名化" },
  { value: "disable_test_users", label: "テストユーザーを無効化" }
] as const;

function statusLabel(status: string) {
  return {
    reported: "報告",
    investigating: "調査中",
    fixing: "対応中",
    resolved: "解決",
    deferred: "保留"
  }[status] || status;
}

export function AdminPilotDashboardPanel() {
  const [dashboard, setDashboard] = useState<PilotDashboardData | null>(null);
  const [report, setReport] = useState<PilotEndReport | null>(null);
  const [adminComment, setAdminComment] = useState("");
  const [issueForm, setIssueForm] = useState({
    category: "その他",
    severity: "medium",
    title: "",
    summary: "",
    reproduction_steps: "",
    assigned_to: ""
  });
  const [maintenanceReason, setMaintenanceReason] = useState("重大障害候補の確認中");
  const [retentionAction, setRetentionAction] = useState<(typeof RETENTION_ACTIONS)[number]["value"]>("keep_summary_only");
  const [retentionConfirm, setRetentionConfirm] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isWorking, setIsWorking] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadDashboard() {
    setIsLoading(true);
    setError("");
    try {
      const response = await getPilotDashboard();
      setDashboard(response.dashboard);
    } catch (caught) {
      setError(toFriendlyError(caught).title);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  const markdownReport = useMemo(() => report?.markdown || "", [report]);
  const issues = dashboard?.issues || [];
  const unresolvedIssues = issues.filter((issue) => !["resolved", "deferred"].includes(issue.status));
  const criticalIncidents = dashboard?.incidents || [];

  async function handleCreateIssue() {
    if (!issueForm.title.trim()) {
      setError("Issueタイトルを入力してください。");
      return;
    }
    setIsWorking(true);
    setError("");
    try {
      await createPilotIssue({
        category: issueForm.category,
        severity: issueForm.severity as "critical" | "high" | "medium" | "low",
        title: issueForm.title,
        summary: issueForm.summary,
        reproduction_steps: issueForm.reproduction_steps,
        assigned_to: issueForm.assigned_to
      });
      setIssueForm({ category: "その他", severity: "medium", title: "", summary: "", reproduction_steps: "", assigned_to: "" });
      setMessage("Issueを登録しました。");
      await loadDashboard();
    } catch (caught) {
      setError(toFriendlyError(caught).title);
    } finally {
      setIsWorking(false);
    }
  }

  async function handleIssueStatus(issue: PilotIssue, status: string) {
    setIsWorking(true);
    setError("");
    try {
      await updatePilotIssue(issue.issue_id, { status: status as PilotIssueStatus });
      setMessage("Issueの状態を更新しました。");
      await loadDashboard();
    } catch (caught) {
      setError(toFriendlyError(caught).title);
    } finally {
      setIsWorking(false);
    }
  }

  async function handleFeedbackToIssue(feedbackId: number) {
    setIsWorking(true);
    setError("");
    try {
      const result = await createPilotIssueFromFeedback(feedbackId, {
        category: "その他",
        severity: "medium",
        title: "フィードバック対応"
      });
      const duplicates = result.duplicate_candidates.length ? ` 重複候補${result.duplicate_candidates.length}件があります。` : "";
      setMessage(`フィードバックをIssue化しました。${duplicates}`);
      await loadDashboard();
    } catch (caught) {
      setError(toFriendlyError(caught).title);
    } finally {
      setIsWorking(false);
    }
  }

  async function handleMaintenance(enabled: boolean) {
    setIsWorking(true);
    setError("");
    try {
      await updatePilotMaintenance(enabled, maintenanceReason);
      setMessage(enabled ? "Maintenance Modeを有効化しました。" : "Maintenance Modeを解除しました。");
      await loadDashboard();
    } catch (caught) {
      setError(toFriendlyError(caught).title);
    } finally {
      setIsWorking(false);
    }
  }

  async function handleEndPilot() {
    setIsWorking(true);
    setError("");
    try {
      const response = await endPilot(adminComment);
      setReport(response.report);
      setDashboard(response.report.dashboard);
      setMessage("Pilot終了レポートを作成しました。");
    } catch (caught) {
      setError(toFriendlyError(caught).title);
    } finally {
      setIsWorking(false);
    }
  }

  async function handleRetention() {
    setIsWorking(true);
    setError("");
    try {
      await applyPilotDataRetention(retentionAction, retentionConfirm);
      setRetentionConfirm("");
      setMessage("Pilotデータ処理を実行しました。本番CRM、Knowledge、監査ログは対象外です。");
      await loadDashboard();
    } catch (caught) {
      setError(toFriendlyError(caught).title);
    } finally {
      setIsWorking(false);
    }
  }

  async function copyReport() {
    if (!markdownReport) return;
    await navigator.clipboard.writeText(markdownReport);
    setMessage("レポートをコピーしました。");
  }

  if (isLoading) {
    return <div className="pilot-dashboard-panel" data-testid="pilot-dashboard-panel">Pilot Dashboardを読み込み中です。</div>;
  }

  if (!dashboard) {
    return (
      <div className="pilot-dashboard-panel" data-testid="pilot-dashboard-panel">
        <strong>Pilot Dashboard</strong>
        <p className="error-text">{error || "Pilot Dashboardを取得できませんでした。"}</p>
        <button className="secondary-button" type="button" onClick={() => void loadDashboard()}>再読み込み</button>
      </div>
    );
  }

  return (
    <section className="pilot-dashboard-panel" data-testid="pilot-dashboard-panel">
      <div className="section-heading compact">
        <p className="eyebrow">Pilot Operations</p>
        <h3>社内試験運用ダッシュボード</h3>
        <p>利用状況、フィードバック、発生中の課題、終了判定だけを確認します。顧客本文や生成本文は保存・表示しません。</p>
      </div>

      {criticalIncidents.length > 0 && (
        <div className="pilot-alert" data-testid="pilot-maintenance-warning">
          <strong>重大障害候補があります</strong>
          <ul>
            {criticalIncidents.map((incident) => (
              <li key={incident.key}>{incident.title}: {incident.detail}</li>
            ))}
          </ul>
        </div>
      )}

      {dashboard.maintenance?.effective && (
        <div className="pilot-alert">
          <strong>Maintenance Mode中です</strong>
          <p>{dashboard.maintenance.reason || "新規作成とPPT/PDF生成を一時停止しています。"}</p>
        </div>
      )}

      {message && <p className="success-text">{message}</p>}
      {error && <p className="error-text">{error}</p>}

      <div className="pilot-metric-grid">
        <article>
          <span>利用者数</span>
          <strong>{dashboard.summary.started_users} / {dashboard.summary.enabled_users}</strong>
        </article>
        <article>
          <span>利用率</span>
          <strong>{dashboard.summary.usage_rate ?? 0}%</strong>
        </article>
        <article>
          <span>成功率</span>
          <strong>{dashboard.summary.success_rate}%</strong>
        </article>
        <article>
          <span>重大エラー数</span>
          <strong>{dashboard.summary.critical_issue_count ?? 0}</strong>
        </article>
        <article>
          <span>未解決Issue数</span>
          <strong>{dashboard.summary.unresolved_issue_count ?? unresolvedIssues.length}</strong>
        </article>
        <article>
          <span>フィードバック平均</span>
          <strong>{dashboard.summary.feedback_average ?? dashboard.feedback_metrics?.average_usability ?? 0}</strong>
        </article>
        <article>
          <span>Pilot終了まで</span>
          <strong>{dashboard.summary.days_to_end ?? "-"}日</strong>
        </article>
      </div>

      <details className="advanced-foldout">
        <summary>利用状況</summary>
        <div className="pilot-user-list">
          {dashboard.users.length === 0 ? (
            <p className="status-note">まだPilot利用者が登録されていません。</p>
          ) : dashboard.users.map((user) => (
            <article key={user.id}>
              <strong>{user.email}</strong>
              <span>{user.role} / 利用 {user.usage_count}回 / 成功 {user.success_count}回 / 失敗 {user.failure_count}回</span>
              <small>最終利用: {user.pilot_last_used_at || "未利用"}</small>
            </article>
          ))}
        </div>
      </details>

      <details className="advanced-foldout">
        <summary>フィードバック</summary>
        <div className="pilot-success-grid">
          <article><strong>使いやすさ平均</strong><span>{dashboard.feedback_metrics?.average_usability ?? 0}/5</span></article>
          <article><strong>実務利用可能</strong><span>{dashboard.feedback_metrics?.practical_usability_rate ?? 0}%</span></article>
          <article><strong>時間短縮実感</strong><span>{dashboard.feedback_metrics?.time_saved_rate ?? 0}%</span></article>
          <article><strong>継続利用意向</strong><span>{dashboard.feedback_metrics?.continue_intent_rate ?? 0}%</span></article>
        </div>
        <div className="pilot-user-list">
          {(dashboard.recent_feedback || []).length === 0 ? (
            <p className="status-note">まだフィードバックはありません。</p>
          ) : dashboard.recent_feedback?.map((feedback) => (
            <article key={feedback.id}>
              <strong>{feedback.rating}</strong>
              <span>{feedback.comment_summary || "コメントなし"}</span>
              <button className="text-button" type="button" onClick={() => void handleFeedbackToIssue(feedback.id)} disabled={isWorking}>
                課題として登録
              </button>
            </article>
          ))}
        </div>
      </details>

      <details className="advanced-foldout" open>
        <summary>発生中の課題</summary>
        <div className="pilot-issue-form">
          <label className="field">
            <span>カテゴリ</span>
            <select value={issueForm.category} onChange={(event) => setIssueForm((current) => ({ ...current, category: event.target.value }))}>
              {ISSUE_CATEGORIES.map((category) => <option key={category} value={category}>{category}</option>)}
            </select>
          </label>
          <label className="field">
            <span>重大度</span>
            <select value={issueForm.severity} onChange={(event) => setIssueForm((current) => ({ ...current, severity: event.target.value }))}>
              {ISSUE_SEVERITIES.map((severity) => <option key={severity} value={severity}>{severity}</option>)}
            </select>
          </label>
          <label className="field">
            <span>タイトル</span>
            <input
              data-testid="pilot-issue-title"
              value={issueForm.title}
              onChange={(event) => setIssueForm((current) => ({ ...current, title: event.target.value }))}
              placeholder="例：要約PPTがダウンロードできない"
            />
          </label>
          <label className="field">
            <span>要約</span>
            <textarea
              value={issueForm.summary}
              onChange={(event) => setIssueForm((current) => ({ ...current, summary: event.target.value }))}
              placeholder="顧客名や本文全文は入れず、現象だけを書いてください"
            />
          </label>
          <button data-testid="pilot-issue-create" className="primary-button" type="button" onClick={() => void handleCreateIssue()} disabled={isWorking}>
            Issueを登録
          </button>
        </div>
        <div className="pilot-user-list">
          {issues.length === 0 ? (
            <p className="status-note">未解決の課題はありません。</p>
          ) : issues.map((issue) => (
            <article key={issue.issue_id}>
              <strong>{issue.issue_id}: {issue.title}</strong>
              <span>{issue.category} / {issue.severity} / {statusLabel(issue.status)}</span>
              <small>{issue.summary || "要約なし"}</small>
              <select value={issue.status} onChange={(event) => void handleIssueStatus(issue, event.target.value)} disabled={isWorking}>
                {ISSUE_STATUSES.map((status) => <option key={status} value={status}>{statusLabel(status)}</option>)}
              </select>
            </article>
          ))}
        </div>
      </details>

      <details className="advanced-foldout" open>
        <summary>終了判定</summary>
        <div className="pilot-end-box">
          <strong data-testid="pilot-judgment-result">{dashboard.judgment?.result || "判定待ち"}</strong>
          <div className="pilot-success-grid">
            {dashboard.success_criteria.map((item) => (
              <article key={item.label} className={item.met ? "is-met" : "needs-attention"}>
                <strong>{item.label}</strong>
                <span>{item.value}{item.unit || ""} / 目標 {item.target}{item.unit || ""}</span>
                <small>{item.met ? "達成" : "要確認"}</small>
              </article>
            ))}
          </div>
          <label className="field">
            <span>管理者コメント</span>
            <textarea value={adminComment} onChange={(event) => setAdminComment(event.target.value)} placeholder="Pilot終了判断に添えるコメント" />
          </label>
          <button className="secondary-button" type="button" onClick={() => void handleEndPilot()} disabled={isWorking}>
            Pilot終了レポートを作成
          </button>
        </div>
      </details>

      <details className="advanced-foldout">
        <summary>重大障害時の停止・データ処理</summary>
        <label className="field">
          <span>停止理由</span>
          <input value={maintenanceReason} onChange={(event) => setMaintenanceReason(event.target.value)} />
        </label>
        <div className="button-row">
          <button data-testid="pilot-maintenance-enable" className="secondary-button" type="button" onClick={() => void handleMaintenance(true)} disabled={isWorking || dashboard.maintenance?.env_enabled}>
            Maintenance Modeを有効化
          </button>
          <button className="secondary-button" type="button" onClick={() => void handleMaintenance(false)} disabled={isWorking || dashboard.maintenance?.env_enabled}>
            Maintenance Modeを解除
          </button>
        </div>
        {dashboard.maintenance?.env_enabled && <p className="status-note">環境変数が優先されているため、画面から解除できません。</p>}

        <div className="pilot-retention-box">
          <strong>削除・匿名化前の対象件数</strong>
          <p>イベント {dashboard.retention_preview?.pilot_events ?? 0}件 / フィードバック {dashboard.retention_preview?.pilot_feedback ?? 0}件 / Issue {dashboard.retention_preview?.pilot_issues ?? 0}件</p>
          <p>本番案件 {dashboard.retention_preview?.production_projects ?? 0}件、Knowledge {dashboard.retention_preview?.knowledge_entries ?? 0}件、監査ログ {dashboard.retention_preview?.audit_logs ?? 0}件は削除対象外です。</p>
          <label className="field">
            <span>処理内容</span>
            <select value={retentionAction} onChange={(event) => setRetentionAction(event.target.value as typeof retentionAction)}>
              {RETENTION_ACTIONS.map((action) => <option key={action.value} value={action.value}>{action.label}</option>)}
            </select>
          </label>
          <label className="field">
            <span>確認文字列</span>
            <input value={retentionConfirm} onChange={(event) => setRetentionConfirm(event.target.value)} placeholder="PILOT と入力" />
          </label>
          <button className="secondary-button" type="button" onClick={() => void handleRetention()} disabled={isWorking || retentionConfirm !== "PILOT"}>
            Pilotデータ処理を実行
          </button>
        </div>
      </details>

      {report && (
        <div className="pilot-end-box">
          <strong>Pilot終了レポート</strong>
          <pre>{markdownReport}</pre>
          <button data-testid="pilot-report-copy" className="secondary-button" type="button" onClick={() => void copyReport()}>
            レポートをコピー
          </button>
        </div>
      )}
    </section>
  );
}
