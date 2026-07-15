"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw, Sparkles } from "lucide-react";
import { FRONTEND_BUILD_INFO, isSameRevision } from "@/lib/buildInfo";
import {
  getBeautifulAiDiagnostics,
  runBeautifulAiConnectionTest,
  type BackendHealthProbe,
  type BeautifulAiConnectionTestResult,
  type BeautifulAiDiagnostics,
  type BeautifulAiStatusProbe
} from "@/lib/beautifulAi";

type BeautifulAiStatusCardProps = {
  statusProbe: BeautifulAiStatusProbe | null;
  healthProbe: BackendHealthProbe | null;
  onRefresh: () => void;
  canViewDiagnostics?: boolean;
};

export function BeautifulAiStatusCard({ statusProbe, healthProbe, onRefresh, canViewDiagnostics = false }: BeautifulAiStatusCardProps) {
  const [diagnostics, setDiagnostics] = useState<BeautifulAiDiagnostics | null>(null);
  const [diagnosticsError, setDiagnosticsError] = useState("");
  const [isDiagnosticsLoading, setIsDiagnosticsLoading] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<BeautifulAiConnectionTestResult | null>(null);

  const routeFound = Boolean((healthProbe?.beautifulAiRouteRegistered ?? true) && (statusProbe?.routeFound ?? false));
  const sameRevision = isSameRevision(FRONTEND_BUILD_INFO.gitCommit, healthProbe?.gitCommit || "");
  const versionMessage =
    sameRevision === false
      ? "FrontendとBackendのバージョンが一致していません。VercelとRenderの最新デプロイを確認してください。"
      : sameRevision === true
        ? "FrontendとBackendは同じコミットです。"
        : "FrontendとBackendのコミット比較は未確認です。";
  const enabled = Boolean(statusProbe?.status?.enabled);
  const mock = Boolean(statusProbe?.status?.mock ?? healthProbe?.beautifulAiMock);
  const apiMode = statusProbe?.status?.api_mode || healthProbe?.beautifulAiApiMode || "";
  const apiModeLabel = apiMode === "structured" ? "Structured API" : apiMode === "prompt" ? "Prompt API" : "未確認";
  const resolvedEndpoint = statusProbe?.status?.resolved_endpoint || healthProbe?.beautifulAiResolvedEndpoint || "未確認";

  const loadDiagnostics = useCallback(async () => {
    if (!canViewDiagnostics) return;
    setIsDiagnosticsLoading(true);
    setDiagnosticsError("");
    try {
      setDiagnostics(await getBeautifulAiDiagnostics());
    } catch (error) {
      setDiagnosticsError(error instanceof Error ? error.message : "Beautiful.ai診断情報を取得できませんでした。");
    } finally {
      setIsDiagnosticsLoading(false);
    }
  }, [canViewDiagnostics]);

  const handleConnectionTest = useCallback(async () => {
    setIsTestingConnection(true);
    setDiagnosticsError("");
    try {
      const result = await runBeautifulAiConnectionTest();
      setTestResult(result);
      await loadDiagnostics();
    } catch (error) {
      setDiagnosticsError(error instanceof Error ? error.message : "Beautiful.ai接続テストに失敗しました。");
    } finally {
      setIsTestingConnection(false);
    }
  }, [loadDiagnostics]);

  useEffect(() => {
    void loadDiagnostics();
  }, [loadDiagnostics]);

  return (
    <section className="beautiful-ai-status-card" data-testid="beautiful-ai-status-card" aria-label="Beautiful.ai接続確認">
      <div className="beautiful-ai-status-heading">
        <div>
          <p className="eyebrow">Production Verification</p>
          <h2><Sparkles size={18} aria-hidden="true" /> Beautiful.ai接続確認</h2>
        </div>
        <button className="secondary-button compact-button" type="button" onClick={onRefresh} data-testid="beautiful-ai-status-refresh">
          <RefreshCw size={14} aria-hidden="true" />
          再確認
        </button>
      </div>

      <div className="beautiful-ai-status-grid">
        <StatusItem label="Enabled" ok={enabled} value={enabled ? "有効" : "無効"} />
        <StatusItem label="Mock" ok={mock} value={mock ? "ON" : "OFF"} neutral={!mock} />
        <StatusItem label="API mode" ok={apiMode === "prompt"} value={apiModeLabel} neutral={apiMode === "structured"} />
        <StatusItem label="API reachable" ok={Boolean(statusProbe?.apiReachable)} value={statusProbe?.apiReachable ? "到達" : "要確認"} />
        <StatusItem label="Route found" ok={Boolean(routeFound)} value={routeFound ? "検出" : "未検出"} />
      </div>

      <div className="beautiful-ai-version-box">
        <div>
          <span>Current backend version</span>
          <strong>{statusProbe?.status?.backend_version || healthProbe?.appVersion || "未確認"} / {healthProbe?.gitCommitShort || "commit未確認"}</strong>
        </div>
        <div>
          <span>Frontend Build Version</span>
          <strong>{FRONTEND_BUILD_INFO.appVersion} / {FRONTEND_BUILD_INFO.gitCommitShort || "commit未設定"}</strong>
        </div>
        <div>
          <span>Build Time</span>
          <strong>{FRONTEND_BUILD_INFO.buildTime || "未設定"}</strong>
        </div>
        <div>
          <span>Beautiful.ai endpoint</span>
          <strong>{resolvedEndpoint}</strong>
        </div>
        <div>
          <span>Last Beautiful.ai result</span>
          <strong>{statusProbe?.status?.last_success_at || statusProbe?.status?.last_error_type || "履歴なし"}</strong>
        </div>
      </div>

      <p className={sameRevision === false ? "beautiful-ai-version-warning" : "beautiful-ai-status-message"}>
        {versionMessage}
      </p>
      <p className={statusProbe?.apiReachable ? "beautiful-ai-status-message" : "beautiful-ai-version-warning"}>
        {statusProbe?.message || "Beautiful.ai status APIは未確認です。"}
      </p>
      <small>確認先: Render /health、Vercel build info、/api/beautiful-ai/status</small>

      {canViewDiagnostics && (
        <div className="beautiful-ai-diagnostics" data-testid="beautiful-ai-diagnostics">
          <div className="beautiful-ai-status-heading">
            <div>
              <p className="eyebrow">Admin Diagnostics</p>
              <h3>Beautiful.ai診断情報</h3>
            </div>
            <button className="secondary-button compact-button" type="button" onClick={handleConnectionTest} disabled={isTestingConnection} data-testid="beautiful-ai-connection-test">
              {isTestingConnection ? "接続テスト中" : "Beautiful.ai接続テスト"}
            </button>
          </div>
          <div className="beautiful-ai-version-box">
            <DiagnosticItem label="API Enabled" value={diagnostics?.enabled ? "有効" : "無効"} />
            <DiagnosticItem label="API Mode" value={diagnostics?.api_mode === "structured" ? "Structured API" : "Prompt API"} />
            <DiagnosticItem label="Resolved Endpoint" value={diagnostics?.resolved_endpoint || resolvedEndpoint} />
            <DiagnosticItem label="Workspace ID" value={diagnostics?.workspace_id || "未設定"} />
            <DiagnosticItem label="Theme ID" value={diagnostics?.theme_id || "未設定"} />
            <DiagnosticItem label="最後のHTTP Status" value={diagnostics?.last_http_status ? String(diagnostics.last_http_status) : "未取得"} />
            <DiagnosticItem label="最後のError Type" value={diagnostics?.last_error_type || "なし"} />
            <DiagnosticItem label="最後の実行日時" value={diagnostics?.last_run_at || "未取得"} />
            <DiagnosticItem label="最後のResponse Text" value={diagnostics?.last_response_text || "なし"} />
          </div>
          {isDiagnosticsLoading && <p className="beautiful-ai-status-message">Beautiful.ai診断情報を取得中です。</p>}
          {testResult && (
            <p className={testResult.ok ? "beautiful-ai-status-message" : "beautiful-ai-version-warning"} data-testid="beautiful-ai-test-result">
              {testResult.message} {testResult.http_status ? `(HTTP ${testResult.http_status})` : ""}
            </p>
          )}
          {diagnosticsError && <p className="beautiful-ai-version-warning">{diagnosticsError}</p>}
          {diagnostics?.history?.length ? (
            <div className="beautiful-ai-history" data-testid="beautiful-ai-history">
              <strong>通信履歴（直近{diagnostics.history.length}件）</strong>
              <ul>
                {diagnostics.history.map((item) => (
                  <li key={item.id}>
                    <span>{item.updated_at || item.created_at}</span>
                    <span>{item.status}</span>
                    <span>HTTP {item.http_status || "-"}</span>
                    <span>{item.error_type || "errorなし"}</span>
                    <span>{item.response_text || "responseなし"}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="beautiful-ai-status-message">通信履歴はまだありません。</p>
          )}
        </div>
      )}
    </section>
  );
}

function StatusItem({ label, ok, value, neutral = false }: { label: string; ok: boolean; value: string; neutral?: boolean }) {
  return (
    <article className={ok ? "is-ok" : neutral ? "is-neutral" : "is-alert"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function DiagnosticItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
