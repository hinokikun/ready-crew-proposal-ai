import type { SemanticAuthority, SemanticReviewState } from "@/types/proposal";

export type M30SourceIdentityDto = {
  source_id: string;
  source_field: string;
  source_reference: string;
};

export type M30CurrentSourceDto = M30SourceIdentityDto & {
  value: string;
};

export type M30CanonicalCandidateDto = {
  candidate_id: string;
  semantic_role: string;
  value: string;
  source_type: string;
  source_field: string;
  source_reference: string;
  source_references: string[];
  source_identities: M30SourceIdentityDto[];
  source_fingerprint: string;
  authority: SemanticAuthority;
  review_state: SemanticReviewState;
  confirmation_authority: SemanticAuthority | null;
  inferred: boolean;
  acquisition_revision: string;
  original_candidate_id: string | null;
};

export type M30CanonicalProposalRequest = {
  semantic_role: string;
  requested_count: number;
  source_records: M30CurrentSourceDto[];
};

export type M30CanonicalProposalResponse = {
  candidates: M30CanonicalCandidateDto[];
};

export type M30CanonicalReviewDecision = {
  original_candidate_id: string;
  action: "CONFIRM" | "CORRECT" | "REJECT";
  corrected_value: string | null;
};

export type M30CanonicalReviewRequest = {
  original_candidate: M30CanonicalCandidateDto;
  current_sources: M30CurrentSourceDto[];
  decision: M30CanonicalReviewDecision;
};

export type M30CanonicalReviewResponse = {
  candidate: M30CanonicalCandidateDto;
};

export type M30CausalityRelationshipProposalDto = {
  relationship_id: string;
  from_id: string;
  to_id: string;
  relationship_type: "causality";
  authority: SemanticAuthority;
  review_state: SemanticReviewState;
  confirmation_authority: SemanticAuthority | null;
  inferred: boolean;
  provenance: string;
};

export type M30CausalityProposalRequest = {
  current_reviewed_nodes: M30CanonicalCandidateDto[];
  current_sources: M30CurrentSourceDto[];
  requested_count: number;
};

export type M30CausalityProposalResponse = {
  relationships: M30CausalityRelationshipProposalDto[];
};

export type M30ReviewedCausalityRelationshipDto = M30CausalityRelationshipProposalDto & {
  original_relationship_id: string;
};

export type M30CausalityReviewDecision = {
  original_relationship_id: string;
  action: "CONFIRM" | "CORRECT" | "REJECT";
  corrected_from_id: string | null;
  corrected_to_id: string | null;
};

export type M30CausalityReviewRequest = {
  original_relationship: M30CausalityRelationshipProposalDto;
  current_reviewed_nodes: M30CanonicalCandidateDto[];
  current_reviewed_relationships: M30ReviewedCausalityRelationshipDto[];
  current_sources: M30CurrentSourceDto[];
  decision: M30CausalityReviewDecision;
};

export type M30CausalityReviewResponse = {
  relationship: M30ReviewedCausalityRelationshipDto;
};
