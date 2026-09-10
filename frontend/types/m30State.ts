import type {
  M30CanonicalCandidateDto,
  M30CausalityRelationshipProposalDto,
  M30ReviewedCausalityRelationshipDto,
} from "@/types/m30Api";

export type M30StateEnvelope = {
  readonly canonicalProposals: readonly M30CanonicalCandidateDto[];
  readonly canonicalReviews: readonly M30CanonicalCandidateDto[];
  readonly relationshipProposals: readonly M30CausalityRelationshipProposalDto[];
  readonly relationshipReviews: readonly M30ReviewedCausalityRelationshipDto[];
  readonly possiblyStale: boolean;
};
