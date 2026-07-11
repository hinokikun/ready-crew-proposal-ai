import { fetchJson } from "@/api/client";
import type { FeedbackEntry, FeedbackRating, FeedbackSummary } from "@/types/app";

export function getFeedback(): Promise<{ feedback: FeedbackEntry[]; summary: FeedbackSummary }> {
  return fetchJson("/api/feedback");
}

export function submitFeedback(payload: {
  rating: FeedbackRating;
  comment: string;
  feature_name: string;
}): Promise<{ feedback: FeedbackEntry; summary: FeedbackSummary }> {
  return fetchJson("/api/feedback", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
