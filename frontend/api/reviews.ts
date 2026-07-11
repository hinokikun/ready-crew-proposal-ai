import { fetchJson } from "@/api/client";
import type { ProposalReviewEntry, ProposalReviewRevision, ProposalReviewStatus } from "@/types/app";

export function listProposalReviews(): Promise<{ reviews: ProposalReviewEntry[] }> {
  return fetchJson("/api/reviews");
}

export function getProposalReview(projectId: string): Promise<{ review: ProposalReviewEntry | null }> {
  return fetchJson(`/api/reviews/${encodeURIComponent(projectId)}`);
}

export function requestProposalReview(payload: { project_id: string; project_name?: string }): Promise<{ ok: boolean; review: ProposalReviewEntry }> {
  return fetchJson("/api/reviews/request", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateProposalReview(
  reviewId: number,
  payload: { status: Extract<ProposalReviewStatus, "approved" | "changes_requested" | "rejected">; review_comment?: string }
): Promise<{ ok: boolean; review: ProposalReviewEntry }> {
  return fetchJson(`/api/reviews/${reviewId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function applyReviewFeedback(
  reviewId: number,
  payload: { current_summary?: string }
): Promise<{ ok: boolean; review: ProposalReviewEntry; ai_improvement_policy: string; diff_summary: string[] }> {
  return fetchJson(`/api/reviews/${reviewId}/apply-feedback`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function rerequestProposalReview(reviewId: number): Promise<{ ok: boolean; review: ProposalReviewEntry }> {
  return fetchJson(`/api/reviews/${reviewId}/rerequest`, {
    method: "POST"
  });
}

export function getProposalReviewRevisions(reviewId: number): Promise<{ revisions: ProposalReviewRevision[] }> {
  return fetchJson(`/api/reviews/${reviewId}/revisions`);
}
