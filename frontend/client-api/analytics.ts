import { fetchJson } from "@/client-api/client";
import type {
  ProductAnalyticsDashboardData,
  ProductAnalyticsEventPayload,
  ReleaseNoteEntry
} from "@/types/app";

export type CandidateBoundaryEvent = {
  event_name: string;
  created_at: string;
  candidate_boundary_correlation_id?: string;
  semantic_candidates_state: string;
  candidate_count: number;
};

export type CandidateBoundaryDiagnosticBoundary = {
  boundary: "ANALYSIS" | "TRANSPORT" | "BACKEND";
  event_name: string;
  physical_row_count: number;
  valid_row_count: number;
  status: "VALID" | "MISSING" | "DUPLICATE" | "INVALID_STATE" | "INVALID_COUNT" | "INVALID_CORRELATION" | "INVALID_METADATA" | "SCOPE_EXCLUDED";
  reason: string;
  scope_match: boolean;
};

export type CandidateBoundaryDiagnostic = {
  requested_correlation_id: string;
  boundaries: CandidateBoundaryDiagnosticBoundary[];
};

export type CandidateBoundaryEventsResponse = {
  events: CandidateBoundaryEvent[];
  diagnostic?: CandidateBoundaryDiagnostic;
};

export const HISTORICAL_CANDIDATE_BOUNDARY_START = "2026-09-02T13:38:00Z";
export const HISTORICAL_CANDIDATE_BOUNDARY_END = "2026-09-02T13:50:00Z";

export function getCandidateBoundaryEvents(start: string, end: string, correlationId?: string): Promise<CandidateBoundaryEventsResponse> {
  const params = new URLSearchParams({ start, end });
  if (correlationId) params.set("candidate_boundary_correlation_id", correlationId);
  return fetchJson(`/api/analytics/candidate-boundary-events?${params.toString()}`);
}

export function getHistoricalCandidateBoundaryEvents(): Promise<CandidateBoundaryEventsResponse> {
  return getCandidateBoundaryEvents(HISTORICAL_CANDIDATE_BOUNDARY_START, HISTORICAL_CANDIDATE_BOUNDARY_END);
}

export function getCandidateBoundaryDiagnosticResult(correlationId: string): Promise<CandidateBoundaryEventsResponse> {
  return fetchJson(`/api/analytics/candidate-boundary-events?candidate_boundary_correlation_id=${encodeURIComponent(correlationId)}`);
}

export function saveProductAnalyticsEvent(payload: ProductAnalyticsEventPayload): Promise<{ ok: boolean }> {
  return fetchJson("/api/analytics/events", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getProductAnalyticsDashboard(
  limit = 20,
  offset = 0
): Promise<{ dashboard: ProductAnalyticsDashboardData }> {
  return fetchJson(`/api/analytics/dashboard?limit=${limit}&offset=${offset}`);
}

export function updateProductAnalyticsErrorResolved(
  errorId: number,
  resolved: boolean
): Promise<{ error: ProductAnalyticsDashboardData["errors"][number] }> {
  return fetchJson(`/api/analytics/errors/${errorId}`, {
    method: "PATCH",
    body: JSON.stringify({ resolved })
  });
}

export function getReleaseNotes(limit = 20, offset = 0): Promise<{ release_notes: ReleaseNoteEntry[] }> {
  return fetchJson(`/api/analytics/release-notes?limit=${limit}&offset=${offset}`);
}

export function createReleaseNote(payload: {
  version: string;
  release_date: string;
  title: string;
  improvements: string;
}): Promise<{ release_note: ReleaseNoteEntry }> {
  return fetchJson("/api/analytics/release-notes", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
