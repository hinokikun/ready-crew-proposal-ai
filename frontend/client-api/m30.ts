import { fetchJson } from "@/client-api/client";
import type {
  M30CanonicalProposalRequest,
  M30CanonicalProposalResponse,
  M30CanonicalReviewRequest,
  M30CanonicalReviewResponse,
  M30CausalityProposalRequest,
  M30CausalityProposalResponse,
  M30CausalityReviewRequest,
  M30CausalityReviewResponse
} from "@/types/m30Api";

export function proposeM30CanonicalNodes(payload: M30CanonicalProposalRequest): Promise<M30CanonicalProposalResponse> {
  return fetchJson("/api/m30/canonical/proposals", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function reviewM30CanonicalNode(payload: M30CanonicalReviewRequest): Promise<M30CanonicalReviewResponse> {
  return fetchJson("/api/m30/canonical/reviews", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function proposeM30CausalityRelationships(payload: M30CausalityProposalRequest): Promise<M30CausalityProposalResponse> {
  return fetchJson("/api/m30/causality/proposals", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function reviewM30CausalityRelationship(payload: M30CausalityReviewRequest): Promise<M30CausalityReviewResponse> {
  return fetchJson("/api/m30/causality/reviews", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
