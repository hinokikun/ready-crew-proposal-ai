import { logger } from "@/lib/logger";
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

const SESSION_STORAGE_KEY = "ai-sales-secretary-analytics-session-v1";
const SAFE_METADATA_KEYS = new Set(["source", "mode", "output", "reason", "category"]);

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
  return Object.fromEntries(
    Object.entries(meta).filter(([key, value]) => SAFE_METADATA_KEYS.has(key) && ["string", "number", "boolean"].includes(typeof value))
  );
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
