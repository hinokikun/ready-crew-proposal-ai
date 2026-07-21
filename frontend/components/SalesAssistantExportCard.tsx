"use client";

import { AlertTriangle, CheckCircle2, ClipboardCopy, Download, FileJson, Loader2, RefreshCcw } from "lucide-react";
import { useMemo, useState } from "react";
import {
  downloadSalesAssistantProposalExport,
  exportSalesAssistantProposal,
  type SalesAssistantExportDownloadResult,
  type SalesAssistantExportPayload,
  type SalesAssistantExportResponse,
  type SalesAssistantExportType,
  type SalesAssistantGeneratePayload,
  type SalesAssistantGenerateResponse,
  type SalesAssistantProposalPreviewResponse,
  type SalesAssistantReviewStatus
} from "@/lib/api";
import { getBeautifulAiOpenUrl } from "@/lib/beautifulAi";

type Props = {
  sourcePayload: SalesAssistantGeneratePayload;
  salesAssistantResult: SalesAssistantGenerateResponse;
  previewResponse: SalesAssistantProposalPreviewResponse;
  enabled: boolean;
  beautifulAiEnabled?: boolean;
};

type ExportHistoryItem = {
  id: string;
  type: SalesAssistantExportType;
  status: "generating" | "downloading" | "success" | "failure";
  label: string;
  message: string;
  startedAt: string;
  completedAt?: string;
  durationMs?: number;
  requestPayload?: SalesAssistantExportPayload;
  response?: SalesAssistantExportResponse;
  download?: SalesAssistantExportDownloadResult;
};

const reviewOptions: Array<{ value: SalesAssistantReviewStatus; label: string; description: string }> = [
  { value: "unreviewed", label: "未レビュー", description: "営業担当者がまだ確認していません。" },
  { value: "reviewed", label: "レビュー済み", description: "内容確認済みです。レビュー必須案件ではExportできません。" },
  { value: "needs_revision", label: "要修正", description: "修正が必要なためExportできません。" },
  { value: "regenerate_recommended", label: "再生成推奨", description: "Proposal Previewの再生成を推奨します。" },
  { value: "approved", label: "Export可能", description: "承認済みとしてExportできます。" }
];

export function SalesAssistantExportCard({
  sourcePayload,
  salesAssistantResult,
  previewResponse,
  enabled,
  beautifulAiEnabled = true
}: Props) {
  const [reviewStatus, setReviewStatus] = useState<SalesAssistantReviewStatus>("unreviewed");
  const [history, setHistory] = useState<ExportHistoryItem[]>([]);
  const [isExporting, setIsExporting] = useState<SalesAssistantExportType | null>(null);
  const [activeDownloadId, setActiveDownloadId] = useState<string | null>(null);
  const [lastType, setLastType] = useState<SalesAssistantExportType | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [showJson, setShowJson] = useState(false);

  const humanReviewRequired = Boolean(
    previewResponse.human_review_required ||
    previewResponse.proposal_preview.human_review_required ||
    salesAssistantResult.human_review_required
  );
  const reviewBlocksExport = reviewStatus === "needs_revision" || reviewStatus === "regenerate_recommended";
  const reviewApproved = reviewStatus === "approved";
  const exportBusy = Boolean(isExporting || activeDownloadId);
  const canExport = enabled && !exportBusy && !reviewBlocksExport && (!humanReviewRequired || reviewApproved);
  const canBeautifulExport = canExport && beautifulAiEnabled;
  const reviewLabel = reviewOptions.find((option) => option.value === reviewStatus)?.label ?? "未レビュー";
  const lastPowerPointSuccess = history.find((item) => item.type === "powerpoint" && item.status === "success" && item.response)?.response;
  const lastBeautifulSuccess = history.find((item) => item.type === "beautiful_ai" && item.status === "success" && item.response)?.response;

  const reviewMessage = useMemo(() => {
    if (!enabled) return "Export機能はFeature Flagで無効です。";
    if (reviewBlocksExport) return "Review結果が要修正または再生成推奨のため、Exportできません。";
    if (humanReviewRequired && !reviewApproved) return "この案件はHuman Review承認後にExportできます。";
    if (reviewApproved) return "Human Review承認済みです。Exportできます。";
    return "Review必須ではないためExportできます。必要に応じて承認してください。";
  }, [enabled, humanReviewRequired, reviewApproved, reviewBlocksExport]);

  function buildExportPayload(type: SalesAssistantExportType): SalesAssistantExportPayload {
    return {
      export_type: type,
      source_request: sourcePayload,
      sales_assistant_brief: salesAssistantResult.sales_assistant_brief,
      strategy_brief: salesAssistantResult.strategy_brief,
      proposal_preview: previewResponse.proposal_preview,
      proposal_response: previewResponse.proposal_response,
      human_review_status: reviewStatus,
      human_review_required: humanReviewRequired,
      project_id: buildProjectId(sourcePayload),
      force_new: false
    };
  }

  async function handleExport(type: SalesAssistantExportType) {
    setError("");
    setNotice("");
    setLastType(type);
    setIsExporting(type);
    const label = type === "powerpoint" ? "PowerPoint" : "Beautiful.ai";
    const id = `${Date.now()}-${type}`;
    const startedAtMs = Date.now();
    const requestPayload = buildExportPayload(type);
    setHistory((current) => [
      {
        id,
        type,
        status: "generating" as const,
        label,
        message: "Exportを開始しました。",
        startedAt: new Date(startedAtMs).toLocaleString("ja-JP"),
        requestPayload
      },
      ...current
    ].slice(0, 5));
    try {
      const response = await exportSalesAssistantProposal(requestPayload);
      const completedAtMs = Date.now();
      setHistory((current) => current.map((item) => item.id === id
        ? {
            ...item,
            status: "success" as const,
            message: response.message,
            completedAt: new Date(completedAtMs).toLocaleString("ja-JP"),
            durationMs: completedAtMs - startedAtMs,
            response
          }
        : item
      ));
      setNotice(`${label} Exportが成功しました。`);
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Exportに失敗しました。";
      const completedAtMs = Date.now();
      setHistory((current) => current.map((item) => item.id === id
        ? {
            ...item,
            status: "failure" as const,
            message,
            completedAt: new Date(completedAtMs).toLocaleString("ja-JP"),
            durationMs: completedAtMs - startedAtMs
          }
        : item
      ));
      setError(message);
    } finally {
      setIsExporting(null);
    }
  }

  async function handleDownload(item: ExportHistoryItem) {
    if (!item.requestPayload) return;
    setError("");
    setNotice("");
    setActiveDownloadId(item.id);
    setHistory((current) => current.map((entry) => entry.id === item.id ? { ...entry, status: "downloading" as const } : entry));
    try {
      const result = await downloadSalesAssistantProposalExport(item.requestPayload);
      setHistory((current) => current.map((entry) => entry.id === item.id
        ? { ...entry, status: "success" as const, download: result }
        : entry
      ));
      setNotice(`PowerPointをダウンロードしました。${result.filename}`);
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "PowerPointのダウンロードに失敗しました。";
      setHistory((current) => current.map((entry) => entry.id === item.id ? { ...entry, status: "failure" as const, message } : entry));
      setError(message);
    } finally {
      setActiveDownloadId(null);
    }
  }

  async function copyText(label: string, text: string) {
    setError("");
    setNotice("");
    try {
      await navigator.clipboard.writeText(text);
      setNotice(`${label}をコピーしました。`);
    } catch {
      setError("コピーできませんでした。ブラウザの権限を確認してください。");
    }
  }

  return (
    <section className="sales-assistant-export-card" aria-label="Proposal Export">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Version 54</p>
          <h2>Human Review & Export</h2>
          <p>Proposal Previewを確認し、承認後に既存PowerPoint生成またはBeautiful.ai生成へ接続します。</p>
        </div>
        <span>{enabled ? "Export Ready" : "Flag OFF"}</span>
      </div>

      <div className={`sales-assistant-review-state ${canExport ? "ok" : "warn"}`} role="status">
        {canExport ? <CheckCircle2 size={18} aria-hidden="true" /> : <AlertTriangle size={18} aria-hidden="true" />}
        <div>
          <strong>レビュー状態: {reviewLabel}</strong>
          <p>{reviewMessage}</p>
        </div>
      </div>

      <div className="sales-assistant-field">
        <label htmlFor="sales-assistant-review-status">Human Review</label>
        <select
          id="sales-assistant-review-status"
          value={reviewStatus}
          onChange={(event) => setReviewStatus(event.target.value as SalesAssistantReviewStatus)}
        >
          {reviewOptions.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <small>{reviewOptions.find((option) => option.value === reviewStatus)?.description}</small>
      </div>

      {notice && <p className="sales-assistant-notice">{notice}</p>}
      {error && (
        <div className="sales-assistant-error" role="alert">
          <AlertTriangle size={18} aria-hidden="true" />
          <div>
            <strong>Exportに失敗しました</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      <div className="sales-assistant-actions">
        <button className="primary-action" type="button" disabled={!canExport} onClick={() => void handleExport("powerpoint")}>
          {isExporting === "powerpoint" ? <Loader2 size={16} aria-hidden="true" /> : null}
          PowerPoint生成
        </button>
        <button className="secondary-action" type="button" disabled={!canBeautifulExport} onClick={() => void handleExport("beautiful_ai")}>
          {isExporting === "beautiful_ai" ? <Loader2 size={16} aria-hidden="true" /> : null}
          Beautiful.ai生成
        </button>
        <button className="secondary-action" type="button" disabled={!lastType || exportBusy} onClick={() => lastType && void handleExport(lastType)}>
          <RefreshCcw size={15} aria-hidden="true" />
          ExportだけRetry
        </button>
      </div>
      {!beautifulAiEnabled && (
        <p className="sales-assistant-muted">Beautiful.ai生成は現在無効です。管理者設定を確認してください。</p>
      )}

      <div className="sales-assistant-copy-grid">
        <button className="secondary-action" type="button" onClick={() => void copyText("Proposal概要", previewResponse.proposal_preview.proposal_summary)}>
          <ClipboardCopy size={15} aria-hidden="true" />
          Proposal概要コピー
        </button>
        <button className="secondary-action" type="button" onClick={() => void copyText("スライド構成", formatSlideOutline(previewResponse))}>
          <ClipboardCopy size={15} aria-hidden="true" />
          スライド構成コピー
        </button>
        <button className="secondary-action" type="button" disabled={!lastPowerPointSuccess?.artifact.download_url} onClick={() => void copyText("PowerPoint生成URL", lastPowerPointSuccess?.artifact.download_url ?? "")}>
          <ClipboardCopy size={15} aria-hidden="true" />
          PowerPoint生成URLコピー
        </button>
        <button className="secondary-action" type="button" disabled={!getBeautifulAiOpenUrl(lastBeautifulSuccess?.artifact)} onClick={() => void copyText("Beautiful.ai URL", getBeautifulAiOpenUrl(lastBeautifulSuccess?.artifact))}>
          <ClipboardCopy size={15} aria-hidden="true" />
          Beautiful.ai URLコピー
        </button>
      </div>

      <div className="sales-assistant-section">
        <h3>Export Status</h3>
        {history.length ? (
          <ol className="sales-assistant-export-history">
            {history.map((item) => (
              <li key={item.id} className={item.status}>
                <strong>{item.label}: {statusLabel(item.status)}</strong>
                <span>開始: {item.startedAt}</span>
                {item.completedAt && <span>完了: {item.completedAt}</span>}
                {item.durationMs !== undefined && <span>処理時間: {formatDuration(item.durationMs)}</span>}
                {item.response?.artifact.filename && <span>ファイル名: {item.response.artifact.filename}</span>}
                {typeof item.response?.artifact.byte_size === "number" && <span>サイズ: {formatBytes(item.response.artifact.byte_size)}</span>}
                {item.download && <span>ダウンロード済み: {item.download.filename} / {formatBytes(item.download.byteSize)}</span>}
                <p>{item.message}</p>
                {item.type === "powerpoint" && item.status === "success" && item.response?.artifact.download_url && item.requestPayload && (
                  <button
                    className="secondary-action"
                    type="button"
                    disabled={activeDownloadId === item.id}
                    onClick={() => void handleDownload(item)}
                  >
                    {activeDownloadId === item.id ? <Loader2 size={15} aria-hidden="true" /> : <Download size={15} aria-hidden="true" />}
                    PowerPointをダウンロード
                  </button>
                )}
                {item.type === "beautiful_ai" && item.status === "success" && getBeautifulAiOpenUrl(item.response?.artifact) && (
                  <a className="secondary-action" href={getBeautifulAiOpenUrl(item.response?.artifact)} target="_blank" rel="noreferrer">
                    Beautiful.aiで開く
                  </a>
                )}
              </li>
            ))}
          </ol>
        ) : (
          <p className="sales-assistant-muted">待機中。Export結果は最新5件だけ画面内に表示します。</p>
        )}
      </div>

      <button className="secondary-action sales-assistant-json-button" type="button" onClick={() => setShowJson((current) => !current)}>
        <FileJson size={16} aria-hidden="true" />
        Export Request / Response JSONを{showJson ? "閉じる" : "開く"}
      </button>
      {showJson && <pre className="sales-assistant-json">{JSON.stringify({ review_status: reviewStatus, history }, null, 2)}</pre>}
    </section>
  );
}

function formatSlideOutline(previewResponse: SalesAssistantProposalPreviewResponse) {
  return previewResponse.proposal_preview.slide_outline
    .map((slide) => `${slide.slide_no}. ${slide.title}\n- ${slide.bullets.join("\n- ")}`)
    .join("\n\n");
}

function buildProjectId(payload: SalesAssistantGeneratePayload) {
  const seed = `${payload.project_title}-${payload.client_name ?? ""}`.trim() || "sales-assistant-proposal";
  return `sales-assistant-${seed}`
    .normalize("NFKC")
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 120);
}

function statusLabel(status: ExportHistoryItem["status"]) {
  if (status === "generating") return "生成中";
  if (status === "downloading") return "ダウンロード中";
  if (status === "success") return "成功";
  return "失敗";
}

function formatDuration(durationMs: number) {
  if (durationMs < 1000) return `${durationMs}ms`;
  return `${(durationMs / 1000).toFixed(1)}秒`;
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)}KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
}
