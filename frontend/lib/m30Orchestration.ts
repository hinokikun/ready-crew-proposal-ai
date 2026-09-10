import {
  proposeM30CanonicalNodes,
  reviewM30CanonicalNode,
  proposeM30CausalityRelationships,
  reviewM30CausalityRelationship,
} from "@/client-api/m30";
import type {
  M30CanonicalCandidateDto,
  M30CanonicalProposalResponse,
  M30CausalityRelationshipProposalDto,
  M30CausalityProposalResponse,
  M30ReviewedCausalityRelationshipDto,
  M30CanonicalReviewResponse,
  M30CausalityReviewResponse,
} from "@/types/m30Api";
import type { M30StateEnvelope } from "@/types/m30State";
import {
  createM30StateEnvelope,
  deriveActiveM30CanonicalCandidates,
  deriveActiveM30Relationships,
  retainM30CanonicalReview,
  retainM30RelationshipReview,
} from "@/lib/m30StateEnvelope";
import { buildM30CurrentSources } from "@/lib/m30CurrentSources";
import type { M30CurrentProductValues } from "@/lib/m30CurrentSources";

export type M30OrchestrationApi = {
  proposeCanonicalNodes: typeof proposeM30CanonicalNodes;
  reviewCanonicalNode: typeof reviewM30CanonicalNode;
  proposeCausalityRelationships: typeof proposeM30CausalityRelationships;
  reviewCausalityRelationship: typeof reviewM30CausalityRelationship;
};

const defaultApi: M30OrchestrationApi = {
  proposeCanonicalNodes: proposeM30CanonicalNodes,
  reviewCanonicalNode: reviewM30CanonicalNode,
  proposeCausalityRelationships: proposeM30CausalityRelationships,
  reviewCausalityRelationship: reviewM30CausalityRelationship,
};

export type M30CanonicalProposalOperationInput = {
  readonly currentValues: M30CurrentProductValues;
  readonly semanticRole: string;
  readonly requestedCount: number;
  readonly envelope: M30StateEnvelope;
};

export type M30CanonicalReviewOperationInput = {
  readonly originalCandidate: M30CanonicalCandidateDto;
  readonly action: "CONFIRM" | "CORRECT" | "REJECT";
  readonly correctedValue?: string;
  readonly currentValues: M30CurrentProductValues;
  readonly envelope: M30StateEnvelope;
};

export type M30RelationshipProposalOperationInput = {
  readonly currentValues: M30CurrentProductValues;
  readonly requestedCount: number;
  readonly envelope: M30StateEnvelope;
};

export type M30RelationshipReviewOperationInput = {
  readonly originalRelationship: M30CausalityRelationshipProposalDto;
  readonly action: "CONFIRM" | "CORRECT" | "REJECT";
  readonly correctedFromId?: string;
  readonly correctedToId?: string;
  readonly currentValues: M30CurrentProductValues;
  readonly envelope: M30StateEnvelope;
};

export async function proposeM30Canonical(
  input: M30CanonicalProposalOperationInput,
  api: M30OrchestrationApi = defaultApi,
): Promise<{ envelope: M30StateEnvelope; response: M30CanonicalProposalResponse }> {
  const response = await api.proposeCanonicalNodes({
    semantic_role: input.semanticRole,
    requested_count: input.requestedCount,
    source_records: buildM30CurrentSources(input.currentValues),
  });
  return {
    response,
    envelope: createM30StateEnvelope({
      ...input.envelope,
      canonicalProposals: [...input.envelope.canonicalProposals, ...response.candidates],
    }),
  };
}

export async function reviewM30Canonical(
  input: M30CanonicalReviewOperationInput,
  api: M30OrchestrationApi = defaultApi,
): Promise<{ envelope: M30StateEnvelope; response: M30CanonicalReviewResponse }> {
  if (input.action === "CORRECT" && (!input.correctedValue || !input.correctedValue.trim())) {
    throw new Error("M30 canonical correction requires a non-empty corrected value");
  }
  const response = await api.reviewCanonicalNode({
    original_candidate: input.originalCandidate,
    current_sources: buildM30CurrentSources(input.currentValues),
    decision: {
      original_candidate_id: input.originalCandidate.candidate_id,
      action: input.action,
      corrected_value: input.action === "CORRECT" ? input.correctedValue! : null,
    },
  });
  return {
    response,
    envelope: retainM30CanonicalReview(input.envelope, response.candidate),
  };
}

export async function proposeM30Relationships(
  input: M30RelationshipProposalOperationInput,
  api: M30OrchestrationApi = defaultApi,
): Promise<{ envelope: M30StateEnvelope; response: M30CausalityProposalResponse }> {
  const response = await api.proposeCausalityRelationships({
    current_reviewed_nodes: deriveActiveM30CanonicalCandidates(input.envelope),
    current_sources: buildM30CurrentSources(input.currentValues),
    requested_count: input.requestedCount,
  });
  return {
    response,
    envelope: createM30StateEnvelope({
      ...input.envelope,
      relationshipProposals: [...input.envelope.relationshipProposals, ...response.relationships],
    }),
  };
}

export async function reviewM30Relationship(
  input: M30RelationshipReviewOperationInput,
  api: M30OrchestrationApi = defaultApi,
): Promise<{ envelope: M30StateEnvelope; response: M30CausalityReviewResponse }> {
  const needsCorrection = input.action === "CORRECT";
  if (needsCorrection && (!input.correctedFromId?.trim() || !input.correctedToId?.trim())) {
    throw new Error("M30 relationship correction requires both corrected endpoints");
  }
  const response = await api.reviewCausalityRelationship({
    original_relationship: input.originalRelationship,
    current_reviewed_nodes: deriveActiveM30CanonicalCandidates(input.envelope),
    current_reviewed_relationships: deriveActiveM30Relationships(input.envelope),
    current_sources: buildM30CurrentSources(input.currentValues),
    decision: {
      original_relationship_id: input.originalRelationship.relationship_id,
      action: input.action,
      corrected_from_id: needsCorrection ? input.correctedFromId! : null,
      corrected_to_id: needsCorrection ? input.correctedToId! : null,
    },
  });
  return {
    response,
    envelope: retainM30RelationshipReview(input.envelope, response.relationship),
  };
}
