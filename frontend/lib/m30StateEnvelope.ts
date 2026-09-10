import type {
  M30CanonicalCandidateDto,
  M30CausalityRelationshipProposalDto,
  M30ReviewedCausalityRelationshipDto,
} from "@/types/m30Api";
import type { M30StateEnvelope } from "@/types/m30State";

const activeReviewStates = new Set(["CONFIRMED", "CORRECTED"]);

export function createM30StateEnvelope(input?: Partial<M30StateEnvelope>): M30StateEnvelope {
  return {
    canonicalProposals: [...(input?.canonicalProposals ?? [])],
    canonicalReviews: [...(input?.canonicalReviews ?? [])],
    relationshipProposals: [...(input?.relationshipProposals ?? [])],
    relationshipReviews: [...(input?.relationshipReviews ?? [])],
    possiblyStale: input?.possiblyStale ?? false,
  };
}

function canonicalReviewBelongsToProposal(
  review: M30CanonicalCandidateDto,
  proposals: readonly M30CanonicalCandidateDto[],
) {
  return Boolean(review.original_candidate_id?.trim()) &&
    proposals.some((proposal) => proposal.candidate_id === review.original_candidate_id);
}

function relationshipReviewBelongsToProposal(
  review: M30ReviewedCausalityRelationshipDto,
  proposals: readonly M30CausalityRelationshipProposalDto[],
) {
  return Boolean(review.original_relationship_id?.trim()) &&
    proposals.some((proposal) => proposal.relationship_id === review.original_relationship_id);
}

export function retainM30CanonicalReview(
  envelope: M30StateEnvelope,
  review: M30CanonicalCandidateDto,
): M30StateEnvelope {
  if (!canonicalReviewBelongsToProposal(review, envelope.canonicalProposals)) {
    throw new Error("M30 canonical review lineage could not be established");
  }
  return createM30StateEnvelope({
    ...envelope,
    canonicalReviews: [...envelope.canonicalReviews, review],
  });
}

export function retainM30RelationshipReview(
  envelope: M30StateEnvelope,
  review: M30ReviewedCausalityRelationshipDto,
): M30StateEnvelope {
  if (!relationshipReviewBelongsToProposal(review, envelope.relationshipProposals)) {
    throw new Error("M30 relationship review lineage could not be established");
  }
  return createM30StateEnvelope({
    ...envelope,
    relationshipReviews: [...envelope.relationshipReviews, review],
  });
}

function isPotentiallyActive(review: { review_state: string; authority: string; confirmation_authority: string | null }) {
  return activeReviewStates.has(review.review_state) &&
    review.authority !== "AI_PROPOSED" &&
    review.authority !== "UNRESOLVED" &&
    review.confirmation_authority === "USER_EXPLICIT";
}

export function deriveActiveM30CanonicalCandidates(
  envelope: M30StateEnvelope,
): M30CanonicalCandidateDto[] {
  return envelope.canonicalReviews.filter(isPotentiallyActive);
}

export function deriveActiveM30Relationships(
  envelope: M30StateEnvelope,
): M30ReviewedCausalityRelationshipDto[] {
  return envelope.relationshipReviews.filter(isPotentiallyActive);
}

export function markM30StatePossiblyStale(envelope: M30StateEnvelope): M30StateEnvelope {
  return envelope.possiblyStale ? envelope : createM30StateEnvelope({ ...envelope, possiblyStale: true });
}
