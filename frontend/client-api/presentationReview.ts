import { fetchJson } from "@/client-api/client";
import type {
  PresentationReview,
  PresentationImprovement,
  PresentationRevision,
  PresentationRevisionChange
} from "@/types/app";
import type { PowerPointData } from "@/types/proposal";

export type PresentationReviewPayload = {
  project_id: string;
  project_name?: string;
  powerpoint_generation_data: PowerPointData;
  beautiful_ai_presentation_id?: string;
};

export function createPresentationReview(payload: PresentationReviewPayload): Promise<{ review: PresentationReview }> {
  return fetchJson("/api/presentation-review/reviews", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getPresentationReviewTimeline(
  projectId: string
): Promise<{ reviews: PresentationReview[]; revisions: PresentationRevision[] }> {
  return fetchJson(`/api/presentation-review/projects/${encodeURIComponent(projectId)}`);
}

export function createPresentationRevision(payload: {
  review_id: number;
  beautiful_ai_presentation_id?: string;
  selected_actions?: PresentationImprovement[];
}): Promise<{ revision: PresentationRevision }> {
  return fetchJson("/api/presentation-review/revisions", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function approvePresentationRevision(revisionId: number, comment = ""): Promise<{ revision: PresentationRevision }> {
  return fetchJson(`/api/presentation-review/revisions/${revisionId}/approve`, {
    method: "PATCH",
    body: JSON.stringify({ comment })
  });
}

export function rejectPresentationRevision(revisionId: number, comment = ""): Promise<{ revision: PresentationRevision }> {
  return fetchJson(`/api/presentation-review/revisions/${revisionId}/reject`, {
    method: "PATCH",
    body: JSON.stringify({ comment })
  });
}

export function generateBeautifulAiRevision(
  revisionId: number,
  beautifulAiPayload: Record<string, unknown>
): Promise<{ revision: PresentationRevision }> {
  return fetchJson(`/api/presentation-review/revisions/${revisionId}/generate-beautiful-ai`, {
    method: "POST",
    body: JSON.stringify({ beautiful_ai_payload: beautifulAiPayload })
  });
}

export function comparePresentationRevisions(
  projectId: string,
  fromRevisionId?: number,
  toRevisionId?: number
): Promise<{ from_revision: PresentationRevision | null; to_revision: PresentationRevision | null; changes: PresentationRevisionChange[] }> {
  const params = new URLSearchParams();
  if (fromRevisionId) params.set("from_revision_id", String(fromRevisionId));
  if (toRevisionId) params.set("to_revision_id", String(toRevisionId));
  const query = params.toString();
  return fetchJson(`/api/presentation-review/projects/${encodeURIComponent(projectId)}/compare${query ? `?${query}` : ""}`);
}
