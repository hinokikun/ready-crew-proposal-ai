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

export function getCandidateBoundaryEvents(start: string, end: string, correlationId?: string): Promise<{ events: CandidateBoundaryEvent[] }> {
  const params = new URLSearchParams({ start, end });
  if (correlationId) params.set("candidate_boundary_correlation_id", correlationId);
  return fetchJson(`/api/analytics/candidate-boundary-events?${params.toString()}`);
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
