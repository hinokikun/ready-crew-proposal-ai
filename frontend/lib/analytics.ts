import { logger } from "@/lib/logger";
import { fetchJson } from "@/client-api/client";
import { getAuthHeaders } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";

export type AnalyticsEvent = {
  name: string;
  feature?: string;
  status?: "success" | "failure" | "start";
  durationMs?: number;
  errorType?: string;
  meta?: Record<string, string | number | boolean | null | undefined>;
};

export type CandidateBoundaryCapture = {
  correlationId: string;
  state: "OMITTED" | "EMPTY" | "NONEMPTY";
  count: number;
};

export type CandidateBoundaryCaptureResult = {
  ok: boolean;
};

export type CandidateBoundaryDiagnosticSession = {
  version: 1;
  correlationId: string;
  phase: "armed" | "analysis_confirmed" | "transport_confirmed" | "completed" | "failed";
  analysisStatus: "pending" | "confirmed" | "failed";
  transportStatus: "pending" | "confirmed" | "failed";
  backendStatus: "pending" | "confirmed" | "failed";
  resultStatus: "pending" | "available" | "invalid";
  createdAt: number;
};

const SESSION_STORAGE_KEY = "ai-sales-secretary-analytics-session-v1";
export const CANDIDATE_BOUNDARY_DIAGNOSTIC_STORAGE_KEY = "ready-crew-candidate-boundary-diagnostic-v2";
const CANDIDATE_BOUNDARY_CORRELATION_PATTERN = /^[a-f0-9]{32}$/i;
const DIAGNOSTIC_SESSION_VERSION = 1;
const DIAGNOSTIC_SESSION_MAX_AGE_MS = 24 * 60 * 60 * 1000;
const SAFE_METADATA_KEYS = new Set(["source", "mode", "output", "reason", "category", "semantic_candidates_state", "candidate_count", "candidate_boundary_correlation_id"]);
const SEMANTIC_CANDIDATE_STATES = new Set(["OMITTED", "EMPTY", "NONEMPTY"]);
const MAX_CANDIDATE_COUNT = 1000;
const MAX_CORRELATION_ID_LENGTH = 64;
const CORRELATION_ID_PATTERN = /^[a-f0-9]{32}$/i;

function createSessionId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function getAnalyticsSessionId() {
  if (typeof window === "undefined") {
    return "server-session";
  }
  const existing = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
  if (existing) {
    return existing;
  }
  const next = createSessionId();
  window.sessionStorage.setItem(SESSION_STORAGE_KEY, next);
  return next;
}

function sanitizeMetadata(meta: AnalyticsEvent["meta"]) {
  if (!meta) {
    return {};
  }
  return Object.fromEntries(Object.entries(meta).filter(([key, value]) => {
    if (!SAFE_METADATA_KEYS.has(key)) return false;
    if (key === "semantic_candidates_state") return typeof value === "string" && SEMANTIC_CANDIDATE_STATES.has(value);
    if (key === "candidate_count") return typeof value === "number" && Number.isInteger(value) && value >= 0 && value <= MAX_CANDIDATE_COUNT;
    return ["string", "number", "boolean"].includes(typeof value);
  }));
}

export function trackEvent(event: AnalyticsEvent) {
  logger.info("analytics:event", {
    name: event.name,
    feature: event.feature,
    status: event.status,
    durationMs: event.durationMs,
    errorType: event.errorType,
    ...sanitizeMetadata(event.meta)
  });

  if (typeof window === "undefined") {
    return;
  }

  window.setTimeout(() => {
    void fetch(`${API_BASE_URL}/api/analytics/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        session_id: getAnalyticsSessionId(),
        event_name: event.name,
        feature_name: event.feature ?? "",
        status: event.status ?? "success",
        duration_ms: Math.max(Math.round(event.durationMs ?? 0), 0),
        error_type: event.errorType ?? "",
        metadata: sanitizeMetadata(event.meta)
      })
    }).catch(() => {
      logger.debug("analytics delivery failed", { name: event.name });
    });
  }, 0);
}

export function createCandidateBoundaryCorrelationId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID().replace(/-/g, "");
  throw new Error("DIAGNOSTIC_CORRELATION_UNAVAILABLE");
}

export function isCandidateBoundaryCorrelationId(value: string): boolean {
  return CANDIDATE_BOUNDARY_CORRELATION_PATTERN.test(value);
}

function isValidDiagnosticSession(value: unknown): value is CandidateBoundaryDiagnosticSession {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<CandidateBoundaryDiagnosticSession>;
  return candidate.version === DIAGNOSTIC_SESSION_VERSION
    && typeof candidate.correlationId === "string"
    && CANDIDATE_BOUNDARY_CORRELATION_PATTERN.test(candidate.correlationId)
    && ["armed", "analysis_confirmed", "transport_confirmed", "completed", "failed"].includes(candidate.phase ?? "")
    && ["pending", "confirmed", "failed"].includes(candidate.analysisStatus ?? "")
    && ["pending", "confirmed", "failed"].includes(candidate.transportStatus ?? "")
    && ["pending", "confirmed", "failed"].includes(candidate.backendStatus ?? "")
    && ["pending", "available", "invalid"].includes(candidate.resultStatus ?? "")
    && typeof candidate.createdAt === "number"
    && Number.isFinite(candidate.createdAt)
    && Date.now() - candidate.createdAt <= DIAGNOSTIC_SESSION_MAX_AGE_MS;
}

export function readCandidateBoundaryDiagnosticSession(): CandidateBoundaryDiagnosticSession | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(CANDIDATE_BOUNDARY_DIAGNOSTIC_STORAGE_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (!isValidDiagnosticSession(parsed)) {
      window.sessionStorage.removeItem(CANDIDATE_BOUNDARY_DIAGNOSTIC_STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    try { window.sessionStorage.removeItem(CANDIDATE_BOUNDARY_DIAGNOSTIC_STORAGE_KEY); } catch { /* fail closed */ }
    return null;
  }
}

export function writeCandidateBoundaryDiagnosticSession(session: CandidateBoundaryDiagnosticSession): void {
  if (typeof window === "undefined" || !isValidDiagnosticSession(session)) return;
  window.sessionStorage.setItem(CANDIDATE_BOUNDARY_DIAGNOSTIC_STORAGE_KEY, JSON.stringify(session));
}

function assertCandidateBoundaryCapture(capture: CandidateBoundaryCapture) {
  if (
    typeof capture.correlationId !== "string" ||
    capture.correlationId.length === 0 ||
    capture.correlationId.length > MAX_CORRELATION_ID_LENGTH ||
    !CORRELATION_ID_PATTERN.test(capture.correlationId) ||
    !SEMANTIC_CANDIDATE_STATES.has(capture.state) ||
    !Number.isInteger(capture.count) ||
    capture.count < 0 ||
    capture.count > MAX_CANDIDATE_COUNT
  ) {
    throw new Error("Invalid candidate boundary capture");
  }
}

export async function persistCandidateBoundaryCapture(
  eventName: "presentation_candidate_boundary_analysis" | "presentation_candidate_boundary_transport",
  capture: CandidateBoundaryCapture,
  timeoutMs = 5000
): Promise<CandidateBoundaryCaptureResult> {
  assertCandidateBoundaryCapture(capture);
  if (typeof window === "undefined") {
    throw new Error("Candidate boundary capture requires a browser");
  }
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const result = await fetchJson<CandidateBoundaryCaptureResult>("/api/analytics/events", {
      method: "POST",
      signal: controller.signal,
      body: JSON.stringify({
        session_id: getAnalyticsSessionId(),
        event_name: eventName,
        feature_name: "proposal",
        status: "success",
        duration_ms: 0,
        error_type: "",
        metadata: {
          candidate_boundary_correlation_id: capture.correlationId,
          semantic_candidates_state: capture.state,
          candidate_count: capture.count
        }
      })
    });
    if (result?.ok !== true) throw new Error("Candidate boundary capture was not acknowledged");
    return result;
  } finally {
    window.clearTimeout(timeout);
  }
}
