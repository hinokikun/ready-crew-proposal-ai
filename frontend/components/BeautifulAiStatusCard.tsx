"use client";

import { RefreshCw, Sparkles } from "lucide-react";
import { FRONTEND_BUILD_INFO, isSameRevision } from "@/lib/buildInfo";
import type { BackendHealthProbe, BeautifulAiStatusProbe } from "@/lib/beautifulAi";

type BeautifulAiStatusCardProps = {
  statusProbe: BeautifulAiStatusProbe | null;
  healthProbe: BackendHealthProbe | null;
  onRefresh: () => void;
};

export function BeautifulAiStatusCard({ statusProbe, healthProbe, onRefresh }: BeautifulAiStatusCardProps) {
  const routeFound = Boolean((healthProbe?.beautifulAiRouteRegistered ?? true) && (statusProbe?.routeFound ?? false));
  const sameRevision = isSameRevision(FRONTEND_BUILD_INFO.gitCommit, healthProbe?.gitCommit || "");
  const versionMessage =
    sameRevision === false
      ? "FrontendとBackendのバージョンが一致していません。VercelまたはRenderの再デプロイを確認してください。"
      : sameRevision === true
        ? "FrontendとBackendは同じコミットです。"
        : "FrontendとBackendのコミット比較は未確認です。";
  const enabled = Boolean(statusProbe?.status?.enabled);
  const mock = Boolean(statusProbe?.status?.mock ?? healthProbe?.beautifulAiMock);
  const apiMode = statusProbe?.status?.api_mode || healthProbe?.beautifulAiApiMode || "";
  const apiModeLabel = apiMode === "structured" ? "Structured API" : apiMode === "prompt" ? "Prompt API" : "未確認";
  const resolvedEndpoint = statusProbe?.status?.resolved_endpoint || healthProbe?.beautifulAiResolvedEndpoint || "未確認";

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
