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

const SESSION_STORAGE_KEY = "ai-sales-secretary-analytics-session-v1";
const SAFE_METADATA_KEYS = new Set(["source", "mode", "output", "reason", "category", "semantic_candidates_state", "candidate_count", "candidate_boundary_correlation_id"]);
const SEMANTIC_CANDIDATE_STATES = new Set(["OMITTED", "EMPTY", "NONEMPTY"]);
const MAX_CANDIDATE_COUNT = 1000;
const MAX_CORRELATION_ID_LENGTH = 64;
const CORRELATION_ID_PATTERN = /^[A-Za-z0-9_-]+$/;

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
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID().replace(/-/g, "");
  }
  return `cb-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 14)}`;
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
    return await fetchJson<CandidateBoundaryCaptureResult>("/api/analytics/events", {
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
  } finally {
    window.clearTimeout(timeout);
  }
}
