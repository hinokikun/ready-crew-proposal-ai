import { fetchJson } from "@/api/client";
import type { ReleaseRecord, ReleaseRecordStatus } from "@/types/app";

export type ReleaseRecordPayload = {
  version: string;
  release_date?: string;
  status?: ReleaseRecordStatus;
  summary?: string;
  changes?: string;
  impact_scope?: string;
  checklist?: string[];
  known_issues?: string;
  rollback_note?: string;
};

export function getReleases(limit = 20): Promise<{ releases: ReleaseRecord[] }> {
  return fetchJson(`/api/releases?limit=${limit}`);
}

export function createReleaseRecord(payload: ReleaseRecordPayload): Promise<{ ok: boolean; release: ReleaseRecord }> {
  return fetchJson("/api/releases", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateReleaseRecord(releaseId: number, payload: Partial<ReleaseRecordPayload>): Promise<{ ok: boolean; release: ReleaseRecord }> {
  return fetchJson(`/api/releases/${releaseId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function publishReleaseRecord(releaseId: number, comment: string): Promise<{ ok: boolean; release: ReleaseRecord }> {
  return fetchJson(`/api/releases/${releaseId}/publish`, {
    method: "POST",
    body: JSON.stringify({ comment })
  });
}
