import { fetchJson } from "@/client-api/client";
import type {
  ProductAnalyticsDashboardData,
  ProductAnalyticsEventPayload,
  ReleaseNoteEntry
} from "@/types/app";

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
