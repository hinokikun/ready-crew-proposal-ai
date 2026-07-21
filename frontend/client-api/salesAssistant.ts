import { fetchJson } from "@/client-api/client";
import { getAuthHeaders } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";
import type {
  SalesAssistantGeneratePayload,
  SalesAssistantGenerateResponse,
  SalesAssistantExportDownloadResult,
  SalesAssistantExportPayload,
  SalesAssistantExportResponse,
  SalesAssistantProposalPreviewPayload,
  SalesAssistantProposalPreviewResponse,
  SalesAssistantStatus
} from "@/types/salesAssistant";

export async function getSalesAssistantStatus(): Promise<SalesAssistantStatus> {
  const response = await fetchJson<unknown>("/api/sales-assistant/status");
  if (!isSalesAssistantStatus(response)) {
    throw new Error("AI営業アシスタントの状態レスポンス形式が不正です");
  }
  return response;
}

export async function generateSalesAssistantBrief(
  payload: SalesAssistantGeneratePayload
): Promise<SalesAssistantGenerateResponse> {
  const response = await fetchJson<unknown>("/api/sales-assistant/generate", {
    method: "POST",
    body: JSON.stringify(payload)
  });
  if (!isSalesAssistantGenerateResponse(response)) {
    throw new Error("AI営業アシスタントの生成レスポンス形式が不正です");
  }
  return response;
}

export async function generateSalesAssistantProposalPreview(
  payload: SalesAssistantProposalPreviewPayload
): Promise<SalesAssistantProposalPreviewResponse> {
  const response = await fetchJson<unknown>("/api/sales-assistant/proposal-preview", {
    method: "POST",
    body: JSON.stringify(payload)
  });
  if (!isSalesAssistantProposalPreviewResponse(response)) {
    throw new Error("Proposal Previewのレスポンス形式が不正です");
  }
  return response;
}

export async function exportSalesAssistantProposal(
  payload: SalesAssistantExportPayload
): Promise<SalesAssistantExportResponse> {
  const response = await fetchJson<unknown>("/api/sales-assistant/export", {
    method: "POST",
    body: JSON.stringify(payload)
  });
  if (!isSalesAssistantExportResponse(response)) {
    throw new Error("Proposal Export response shape is invalid.");
  }
  return response;
}

export async function downloadSalesAssistantProposalExport(
  payload: SalesAssistantExportPayload
): Promise<SalesAssistantExportDownloadResult> {
  const timeout = createDownloadTimeoutSignal();
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/sales-assistant/export/download`, {
      method: "POST",
      signal: timeout.signal,
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      },
      body: JSON.stringify(payload)
    });
  } catch (caught) {
    if (caught instanceof DOMException && caught.name === "AbortError") {
      throw new Error("PowerPoint download failed: 通信がタイムアウトしました。時間をおいて再試行してください。");
    }
    throw caught;
  } finally {
    timeout.dispose();
  }

  if (!response.ok) {
    throw new Error(await readDownloadError(response));
  }

  const blob = await response.blob();
  if (blob.size <= 0) {
    throw new Error("PowerPoint download failed: ファイルが空です。Exportを再試行してください。");
  }

  const filename = filenameFromDisposition(response.headers.get("content-disposition")) || fallbackFilename(payload);
  const url = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.rel = "noopener";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  return {
    filename,
    byteSize: blob.size,
    contentType: blob.type || response.headers.get("content-type") || "application/vnd.openxmlformats-officedocument.presentationml.presentation"
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isSalesAssistantStatus(value: unknown): value is SalesAssistantStatus {
  if (!isRecord(value)) return false;
  return (
    typeof value.enabled === "boolean" &&
    typeof value.version === "string" &&
    typeof value.requires_admin === "boolean" &&
    typeof value.persistence_enabled === "boolean" &&
    typeof value.external_ai_enabled === "boolean" &&
    (typeof value.proposal_preview_enabled === "boolean" || value.proposal_preview_enabled === undefined) &&
    (typeof value.proposal_export_enabled === "boolean" || value.proposal_export_enabled === undefined) &&
    (typeof value.beautiful_ai_export_enabled === "boolean" || value.beautiful_ai_export_enabled === undefined)
  );
}

function isSalesAssistantGenerateResponse(value: unknown): value is SalesAssistantGenerateResponse {
  if (!isRecord(value)) return false;
  if (!isRecord(value.sales_assistant_brief)) return false;
  if (!isRecord(value.generation_metadata)) return false;
  const brief = value.sales_assistant_brief;
  return (
    isRecord(brief.summary) &&
    isRecord(brief.meeting_plan) &&
    Array.isArray(brief.discovery_questions) &&
    isRecord(brief.talk_track) &&
    Array.isArray(brief.objection_handling) &&
    isRecord(brief.decision_maker_support) &&
    isRecord(brief.evidence_guidance) &&
    Array.isArray(brief.next_actions) &&
    isRecord(brief.follow_up) &&
    isRecord(brief.risk_and_guardrails) &&
    isRecord(brief.generation_metadata) &&
    isRecord(value.strategy_brief_summary) &&
    isStringArray(value.warnings) &&
    typeof value.human_review_required === "boolean" &&
    isStringArray(value.human_review_reasons)
  );
}

function isSalesAssistantProposalPreviewResponse(value: unknown): value is SalesAssistantProposalPreviewResponse {
  if (!isRecord(value)) return false;
  if (!isRecord(value.proposal_preview)) return false;
  if (!isRecord(value.generation_metadata)) return false;
  const preview = value.proposal_preview;
  return (
    typeof preview.proposal_summary === "string" &&
    Array.isArray(preview.issues) &&
    typeof preview.proposal_story === "string" &&
    typeof preview.proposal_policy === "string" &&
    Array.isArray(preview.slide_outline) &&
    isStringArray(preview.kpis) &&
    typeof preview.estimate_summary === "string" &&
    typeof preview.deck_title === "string" &&
    typeof preview.client_name === "string" &&
    typeof preview.human_review_required === "boolean" &&
    isStringArray(preview.human_review_reasons) &&
    typeof value.human_review_required === "boolean" &&
    isStringArray(value.human_review_reasons) &&
    typeof value.generation_metadata.schema_version === "string"
  );
}

function isSalesAssistantExportResponse(value: unknown): value is SalesAssistantExportResponse {
  if (!isRecord(value)) return false;
  return (
    (value.export_type === "powerpoint" || value.export_type === "beautiful_ai") &&
    typeof value.status === "string" &&
    typeof value.message === "string" &&
    isRecord(value.artifact) &&
    isRecord(value.request_json_safe) &&
    isRecord(value.response_json_safe)
  );
}

function createDownloadTimeoutSignal(): { signal?: AbortSignal; dispose: () => void } {
  if (typeof AbortController === "undefined") {
    return { signal: undefined, dispose: () => undefined };
  }
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 60000);
  return {
    signal: controller.signal,
    dispose: () => window.clearTimeout(timer)
  };
}

async function readDownloadError(response: Response): Promise<string> {
  try {
    const body = await response.json() as { detail?: string | { message?: string }; message?: string };
    const detailMessage = typeof body.detail === "string" ? body.detail : body.detail?.message;
    return `PowerPoint download failed: ${body.message || detailMessage || `status=${response.status}`}`;
  } catch {
    return `PowerPoint download failed: status=${response.status}`;
  }
}

function filenameFromDisposition(disposition: string | null): string {
  if (!disposition) return "";
  const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
  if (encoded) {
    try {
      return sanitizeDownloadFilename(decodeURIComponent(encoded));
    } catch {
      return "";
    }
  }
  const plain = disposition.match(/filename="([^"]+)"/i)?.[1] || disposition.match(/filename=([^;]+)/i)?.[1];
  return plain ? sanitizeDownloadFilename(plain) : "";
}

function fallbackFilename(payload: SalesAssistantExportPayload): string {
  const source = payload.source_request.project_title || payload.proposal_preview.deck_title || "proposal";
  return sanitizeDownloadFilename(`ProposalPilot_${source}.pptx`);
}

function sanitizeDownloadFilename(value: string): string {
  const normalized = value.normalize("NFKC").replace(/[\\/:*?"<>|\u0000-\u001f]+/g, "_").trim();
  const filename = normalized.endsWith(".pptx") ? normalized : `${normalized || "ProposalPilot_proposal"}.pptx`;
  return filename.slice(0, 140);
}
