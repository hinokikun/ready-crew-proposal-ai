import { getAuthHeaders } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";
import type { PowerPointData } from "@/types/proposal";

export type ReleaseJudge = "NOT_READY" | "REVIEW_REQUIRED" | "CUSTOMER_READY";

export type ProposalValidationResult = {
  release_judge: ReleaseJudge;
  summary: string;
  acceptance_scores: {
    customer_ready_score: number;
    executive_score: number;
    sales_score: number;
    technical_score: number;
    presentation_score: number;
    visual_score: number;
    business_value_score: number;
    total_score: number;
  };
  human_acceptance_prediction: {
    no_revision_probability: number;
    thirty_min_revision_probability: number;
    rationale: string[];
  };
  persona_reviews: Array<{
    persona: string;
    score: number;
    verdict: string;
    thoughts: string[];
    strengths: string[];
    concerns: string[];
    required_fixes: string[];
  }>;
  benchmark_reviews: Array<{
    benchmark: string;
    score: number;
    structure: number;
    story: number;
    readability: number;
    persuasion: number;
    notes: string[];
  }>;
  red_team_findings: Array<{
    severity: string;
    issue: string;
    impact: string;
    improvement: string;
  }>;
  customer_questions: Array<{ question: string; answer: string }>;
  slide_reviews: Array<{
    slide_no: number;
    title: string;
    has_conclusion: boolean;
    text_volume: string;
    readability_score: number;
    design_score: number;
    persuasion_score: number;
    improvement: string;
  }>;
  visual_qa_findings: Array<{
    slide_no: number;
    category: string;
    severity: string;
    message: string;
    recommendation: string;
  }>;
  regression_quality: {
    baseline: string;
    improvements: Record<string, number>;
    average_improvement_rate: number;
  };
  required_fixes: string[];
};

export async function validateProposalForAcceptance(
  powerpointData: PowerPointData,
  proposalContext: Record<string, unknown> = {}
): Promise<ProposalValidationResult> {
  const response = await fetch(`${API_BASE_URL}/api/proposal-validation/validate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({
      powerpoint_generation_data: powerpointData,
      proposal_context: proposalContext
    })
  });

  if (!response.ok) {
    throw new Error(await readValidationError(response));
  }

  const body = (await response.json()) as { validation: ProposalValidationResult };
  return body.validation;
}

async function readValidationError(response: Response) {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
    if (body.detail && typeof body.detail === "object") return "提出可否チェックを完了できませんでした。";
  } catch {
    // Fall through to the safe generic message.
  }
  if (response.status === 401 || response.status === 403) {
    return "ログイン状態または権限を確認してください。";
  }
  return "提出可否チェックを完了できませんでした。時間を置いて再度お試しください。";
}
