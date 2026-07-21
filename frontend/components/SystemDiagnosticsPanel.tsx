"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, ChevronDown, Clock3, RefreshCw, ShieldCheck } from "lucide-react";
import {
  getAdminAiLogs,
  getEnvironmentChecks,
  getProposalGenerationHistory,
  getSystemDiagnostics,
  runConnectionTests,
  runSystemSelfCheck,
  type AdminAiLogItem,
  type EnvironmentCheckItem,
  type EnvironmentCheckStatus,
  type ProposalGenerationHistoryItem,
  type SystemCheckRun,
  type SystemDiagnostics,
  type SystemDiagnosticStatus
} from "@/lib/systemDiagnostics";

const statusLabels: Record<SystemDiagnosticStatus, string> = {
  ok: "正常",
  warning: "注意",
  error: "エラー",
  skipped: "未実行",
  unknown: "未確認"
};

const environmentLabels: Record<EnvironmentCheckStatus, string> = {
  configured: "設定済み",
  missing: "未設定",
  invalid: "要確認",
  disabled: "無効",
  optional: "任意",
  unknown: "未確認"
};

const connectionTargets = [
  { key: "backend", label: "Backend" },
  { key: "database", label: "Database" },
  { key: "auth", label: "Auth" },
  { key: "openai", label: "OpenAI" },
  { key: "beautiful_ai", label: "Beautiful.ai" },
  { key: "pptx", label: "PPTX" },
  { key: "pdf", label: "PDF" }
];

export function SystemDiagnosticsPanel() {
  const [diagnostics, setDiagnostics] = useState<SystemDiagnostics | null>(null);
  const [selfCheck, setSelfCheck] = useState<SystemCheckRun | null>(null);
  const [connectionRun, setConnectionRun] = useState<SystemCheckRun | null>(null);
  const [environment, setEnvironment] = useState<EnvironmentCheckItem[]>([]);
  const [aiLogs, setAiLogs] = useState<AdminAiLogItem[]>([]);
  const [history, setHistory] = useState<ProposalGenerationHistoryItem[]>([]);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");

  async function refreshSummary() {
    setLoading("summary");
    setError("");
    try {
      const [nextDiagnostics, nextEnvironment] = await Promise.all([getSystemDiagnostics(), getEnvironmentChecks()]);
      setDiagnostics(nextDiagnostics);
      setEnvironment(nextEnvironment.items);
    } catch {
      setDiagnostics(null);
      setError("Backendに接続できません。Backendが起動しているか確認してください。");
    } finally {
      setLoading("");
    }
  }

  async function handleSelfCheck() {
    if (loading) return;
    setLoading("self-check");
    setError("");
    try {
      setSelfCheck(await runSystemSelfCheck());
    } catch {
      setError("自己診断を実行できませんでした。ログイン状態とBackendを確認してください。");
    } finally {
      setLoading("");
    }
  }

  async function handleConnectionTest(checks: string[] = []) {
    if (loading) return;
    setLoading(checks.length === 1 ? `connection-${checks[0]}` : "connection-all");
    setError("");
    try {
      setConnectionRun(await runConnectionTests(checks));
    } catch {
      setError("接続テストを実行できませんでした。Backendと権限を確認してください。");
    } finally {
      setLoading("");
    }
  }

  async function loadAiLogs() {
    setLoading("ai-logs");
    setError("");
    try {
      const response = await getAdminAiLogs();
      setAiLogs(response.items);
    } catch {
      setError("AIログを取得できませんでした。権限またはBackendを確認してください。");
    } finally {
      setLoading("");
    }
  }

  async function loadHistory() {
    setLoading("history");
    setError("");
    try {
      const response = await getProposalGenerationHistory();
      setHistory(response.items);
    } catch {
      setError("提案書生成履歴を取得できませんでした。権限またはBackendを確認してください。");
    } finally {
      setLoading("");
    }
  }

  useEffect(() => {
    void refreshSummary();
  }, []);

  const summaryText = useMemo(() => {
    if (!diagnostics) return "未確認";
    const okCount = diagnostics.checks.filter((item) => item.status === "ok").length;
    return `${okCount}/${diagnostics.checks.length} OK`;
  }, [diagnostics]);

  const isBusy = Boolean(loading);

  return (
    <section className="system-ops-panel" data-testid="system-ops-panel" aria-label="管理者向けシステム運用チェック">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Operations</p>
          <h2>システム状態サマリー</h2>
          <p>Backend、DB、認証、OpenAI、Beautiful.ai、生成機能の状態を安全に確認します。秘密情報は表示しません。</p>
        </div>
        <button className="secondary-button" type="button" onClick={() => void refreshSummary()} disabled={loading === "summary"}>
          <RefreshCw size={16} aria-hidden="true" />
          {loading === "summary" ? "確認中" : "再チェック"}
        </button>
      </div>
      {error && <p className="beautiful-ai-error" role="alert">{error}</p>}

      <div className="operation-summary-grid">
        <article className={diagnostics?.overall_status === "ok" ? "is-ok" : "is-alert"}>
          <ShieldCheck size={18} aria-hidden="true" />
          <span>総合状態</span>
          <strong>{diagnostics ? statusLabels[diagnostics.overall_status] : "未確認"}</strong>
          <p>{summaryText}</p>
        </article>
        <article>
          <Clock3 size={18} aria-hidden="true" />
          <span>Backend Version</span>
          <strong>{diagnostics?.backend.version || "未確認"}</strong>
          <p>{diagnostics?.frontend.api_base_url || "API Base URL未確認"}</p>
        </article>
        <article>
          <CheckCircle2 size={18} aria-hidden="true" />
          <span>Beautiful.ai</span>
          <strong>{diagnostics?.beautiful_ai.configured ? "設定済み" : "要確認"}</strong>
          <p>Mode: {diagnostics?.beautiful_ai.api_mode || "未確認"}</p>
        </article>
      </div>

      <details className="advanced-foldout" open>
        <summary><ChevronDown size={16} aria-hidden="true" /> システム自己診断</summary>
        <div className="operation-section">
          <button className="primary-action" type="button" onClick={() => void handleSelfCheck()} disabled={isBusy}>
            {loading === "self-check" ? "診断中" : "システム自己診断を実行"}
          </button>
          {selfCheck && <RunSummary run={selfCheck} />}
          <CheckGrid checks={selfCheck?.checks ?? diagnostics?.checks ?? []} />
        </div>
      </details>

      <details className="advanced-foldout">
        <summary><ChevronDown size={16} aria-hidden="true" /> 接続テスト</summary>
        <div className="operation-section">
          <button className="secondary-button" type="button" onClick={() => void handleConnectionTest()} disabled={isBusy}>
            {loading === "connection-all" ? "全件テスト中" : "全件テスト"}
          </button>
          <div className="operation-button-grid">
            {connectionTargets.map((target) => (
              <button
                className="secondary-button"
                type="button"
                key={target.key}
                onClick={() => void handleConnectionTest([target.key])}
                disabled={isBusy}
              >
                {loading === `connection-${target.key}` ? "確認中" : target.label}
              </button>
            ))}
          </div>
          {connectionRun && <RunSummary run={connectionRun} />}
          <CheckGrid checks={connectionRun?.checks ?? []} />
        </div>
      </details>

      <details className="advanced-foldout">
        <summary><ChevronDown size={16} aria-hidden="true" /> 環境変数チェック</summary>
        <div className="operation-section">
          <EnvironmentTable items={environment} />
        </div>
      </details>

      <details className="advanced-foldout">
        <summary><ChevronDown size={16} aria-hidden="true" /> 提案書生成履歴</summary>
        <div className="operation-section">
          <button className="secondary-button" type="button" onClick={() => void loadHistory()} disabled={loading === "history"}>
            {loading === "history" ? "読み込み中" : "履歴を読み込む"}
          </button>
          <HistoryTable items={history} />
        </div>
      </details>

      <details className="advanced-foldout">
        <summary><ChevronDown size={16} aria-hidden="true" /> AIログビューア</summary>
        <div className="operation-section">
          <button className="secondary-button" type="button" onClick={() => void loadAiLogs()} disabled={loading === "ai-logs"}>
            {loading === "ai-logs" ? "読み込み中" : "AIログを読み込む"}
          </button>
          <AiLogTable items={aiLogs} />
        </div>
      </details>
    </section>
  );
}

function RunSummary({ run }: { run: SystemCheckRun }) {
  return (
    <div className="operation-run-summary" aria-live="polite">
      <strong>{run.summary.ok}/{run.summary.total} OK</strong>
      <span>注意 {run.summary.warning}</span>
      <span>エラー {run.summary.error}</span>
      <span>未実行 {run.summary.skipped}</span>
      <span>{run.duration_ms}ms</span>
    </div>
  );
}

function CheckGrid({ checks }: { checks: Array<{ name: string; label?: string; status: SystemDiagnosticStatus; message: string; action?: string; duration_ms?: number }> }) {
  if (!checks.length) {
    return <p className="admin-feedback-empty">まだ確認結果はありません。</p>;
  }
  return (
    <div className="trial-check-grid">
      {checks.map((item) => (
        <article className={item.status === "ok" ? "is-ok" : "is-alert"} key={item.name}>
          {item.status === "ok" ? <CheckCircle2 size={18} aria-hidden="true" /> : <AlertCircle size={18} aria-hidden="true" />}
          <div>
            <strong>{item.label || item.name} <small>{statusLabels[item.status]}</small></strong>
            <p>{item.message}</p>
            {item.action ? <p className="operation-action">{item.action}</p> : null}
            {typeof item.duration_ms === "number" ? <span>{item.duration_ms}ms</span> : null}
          </div>
        </article>
      ))}
    </div>
  );
}

function EnvironmentTable({ items }: { items: EnvironmentCheckItem[] }) {
  if (!items.length) {
    return <p className="admin-feedback-empty">環境変数チェックは未取得です。</p>;
  }
  return (
    <div className="usage-dashboard-table-wrap">
      <table className="usage-dashboard-table">
        <thead>
          <tr><th>項目</th><th>分類</th><th>状態</th><th>次の対応</th></tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.name}>
              <td>{item.name}</td>
              <td>{item.required ? "必須" : item.category === "recommended" ? "推奨" : "任意"}</td>
              <td>{environmentLabels[item.status] ?? "未確認"}</td>
              <td>{item.action || item.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function HistoryTable({ items }: { items: ProposalGenerationHistoryItem[] }) {
  if (!items.length) {
    return <p className="admin-feedback-empty">履歴はまだ読み込まれていないか、0件です。</p>;
  }
  return (
    <div className="usage-dashboard-table-wrap">
      <table className="usage-dashboard-table">
        <thead>
          <tr><th>生成日時</th><th>ユーザー</th><th>案件</th><th>出力</th><th>状態</th><th>リンク</th></tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.created_at}</td>
              <td>{item.user || "未記録"}</td>
              <td>{item.project_title || item.project_id || "未記録"}</td>
              <td>{item.output_type}</td>
              <td>{item.status}{item.error_type ? ` / ${item.error_type}` : ""}</td>
              <td>{item.open_url ? <a href={item.open_url} target="_blank" rel="noreferrer">開く</a> : "なし"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AiLogTable({ items }: { items: AdminAiLogItem[] }) {
  if (!items.length) {
    return <p className="admin-feedback-empty">AIログはまだ読み込まれていないか、0件です。</p>;
  }
  return (
    <div className="usage-dashboard-table-wrap">
      <table className="usage-dashboard-table">
        <thead>
          <tr><th>日時</th><th>provider</th><th>operation</th><th>status</th><th>user</th><th>request_id</th><th>概要</th></tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.created_at}</td>
              <td>{item.provider}</td>
              <td>{item.operation}</td>
              <td>{item.status}{item.error_type ? ` / ${item.error_type}` : ""}</td>
              <td>{item.user || "未記録"}</td>
              <td>{item.request_id || "-"}</td>
              <td>{item.summary}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
