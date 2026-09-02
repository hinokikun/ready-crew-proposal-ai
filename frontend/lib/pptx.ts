import type { PowerPointData, SemanticCandidate, WinProbability } from "@/types/proposal";
import { getAuthHeaders } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";
import { trackEvent } from "@/lib/analytics";

type DownloadPptxPayload = {
  powerpoint_generation_data: PowerPointData;
  win_probability?: WinProbability;
  project_brief?: string;
  client_company_info?: string;
  competitor_site_url?: string;
  competitor_company_name?: string;
  estimated_page_count?: string;
  cms_required?: string;
  contact_form_required?: string;
  special_function_required?: string;
  seo_required?: string;
  content_creation_required?: string;
  desired_launch_timing?: string;
  budget_range?: string;
  own_service_info?: string;
  past_proposal_template?: string;
  case_studies?: string;
  summary?: boolean;
  design_template?: string;
  brand_settings?: Record<string, string>;
  presentation_quality_state?: PresentationQualityRequestState;
  presentation_layout_decisions?: PresentationLayoutDecisionRequest[];
  semantic_confirmation_state?: SemanticConfirmationTransportItem[];
  semantic_candidates?: { candidates: SemanticCandidate[] };
};

type PowerPointDesignOptions = {
  designTemplate?: string;
  brandSettings?: Record<string, string>;
  qualityState?: PresentationQualityRequestState;
  layoutDecisions?: PresentationLayoutDecisionRequest[];
  semanticCandidates?: SemanticCandidate[];
};

export type SemanticConfirmationTransportItem = Pick<SemanticCandidate, "id" | "semantic_type" | "review_state"> & {
  value?: string;
};

export type PresentationQualityRequestState = {
  applied_fixes: string[];
  rejected_fixes: string[];
  pending_fix_count: number;
  source: "proposal_studio" | "legacy";
};

export type PresentationLayoutDecisionRequest = {
  slide_id: string;
  slide_index?: number;
  slide_type: string;
  selected_layout_id: string;
  recommended_layout_ids: string[];
  selection_reason: string;
  expected_effect: string;
  template_id: string;
  design_token_id: string;
  applied_by: "user" | "designer_ai" | "quality_engine" | "backend_fallback";
  status: "suggested" | "applied" | "rejected" | "backend_fallback" | "unsupported";
  confidence: number;
  human_review_required: boolean;
};

export type PresentationQualityDownloadReport = {
  overall_score: number;
  category_scores: Record<string, number>;
  findings: Array<{
    rule_id: string;
    category: string;
    severity: "info" | "warning" | "critical";
    message: string;
    recommendation: string;
    slide_no?: number | null;
    slide_title?: string;
    auto_fixable?: boolean;
    human_review_required?: boolean;
  }>;
  auto_fixes_applied: Array<{ rule_id: string; message: string; slide_title?: string }>;
  warnings: string[];
  human_review_required: boolean;
  slide_count_before: number;
  slide_count_after: number;
  template: string;
  generation_duration: number;
  layout_decisions?: Array<Record<string, unknown>>;
  layout_fallbacks?: Array<Record<string, unknown>>;
  preview_pptx_differences?: Array<Record<string, unknown>>;
  predicted_score?: number | null;
  rendered_score?: number | null;
  score_delta?: number | null;
  unsupported_layouts?: string[];
  numeric_integrity?: {
    preserved?: boolean;
    checked_slide_count?: number;
    mismatches?: Array<Record<string, unknown>>;
  };
  template_token_application?: Record<string, unknown>;
  human_review_items?: string[];
  customer_ready_status?: "READY" | "REVIEW_REQUIRED" | "BLOCKED" | "";
  customer_ready_score?: number | null;
  customer_ready_reasons?: string[];
  customer_ready_blockers?: string[];
  customer_ready_auto_fixes?: string[];
  customer_ready_excluded_internal_items?: string[];
  customer_ready_sales_summary?: string[];
  customer_ready_expected_questions?: Array<{ question: string; answer: string }>;
  customer_ready_rubric?: Record<string, number>;
};

export type PowerPointDownloadResult = {
  filename: string;
  qualityReport: PresentationQualityDownloadReport | null;
};

export async function downloadProposalPowerPoint(
  data: PowerPointData,
  winProbability?: WinProbability,
  projectBrief = "",
  clientCompanyInfo = "",
  competitorSiteUrl = "",
  competitorCompanyName = "",
  estimatedPageCount = "",
  cmsRequired = "",
  contactFormRequired = "",
  specialFunctionRequired = "",
  seoRequired = "",
  contentCreationRequired = "",
  desiredLaunchTiming = "",
  budgetRange = "",
  ownServiceInfo = "",
  pastProposalTemplate = "",
  caseStudies = "",
  options: PowerPointDesignOptions = {}
): Promise<PowerPointDownloadResult> {
  return downloadPowerPoint(
    data,
    winProbability,
    projectBrief,
    clientCompanyInfo,
    competitorSiteUrl,
    competitorCompanyName,
    estimatedPageCount,
    cmsRequired,
    contactFormRequired,
    specialFunctionRequired,
    seoRequired,
    contentCreationRequired,
    desiredLaunchTiming,
    budgetRange,
    ownServiceInfo,
    pastProposalTemplate,
    caseStudies,
    false,
    options
  );
}

export async function downloadSummaryProposalPowerPoint(
  data: PowerPointData,
  winProbability?: WinProbability,
  projectBrief = "",
  clientCompanyInfo = "",
  competitorSiteUrl = "",
  competitorCompanyName = "",
  estimatedPageCount = "",
  cmsRequired = "",
  contactFormRequired = "",
  specialFunctionRequired = "",
  seoRequired = "",
  contentCreationRequired = "",
  desiredLaunchTiming = "",
  budgetRange = "",
  ownServiceInfo = "",
  pastProposalTemplate = "",
  caseStudies = "",
  options: PowerPointDesignOptions = {}
): Promise<PowerPointDownloadResult> {
  return downloadPowerPoint(
    data,
    winProbability,
    projectBrief,
    clientCompanyInfo,
    competitorSiteUrl,
    competitorCompanyName,
    estimatedPageCount,
    cmsRequired,
    contactFormRequired,
    specialFunctionRequired,
    seoRequired,
    contentCreationRequired,
    desiredLaunchTiming,
    budgetRange,
    ownServiceInfo,
    pastProposalTemplate,
    caseStudies,
    true,
    options
  );
}

async function downloadPowerPoint(
  data: PowerPointData,
  winProbability?: WinProbability,
  projectBrief = "",
  clientCompanyInfo = "",
  competitorSiteUrl = "",
  competitorCompanyName = "",
  estimatedPageCount = "",
  cmsRequired = "",
  contactFormRequired = "",
  specialFunctionRequired = "",
  seoRequired = "",
  contentCreationRequired = "",
  desiredLaunchTiming = "",
  budgetRange = "",
  ownServiceInfo = "",
  pastProposalTemplate = "",
  caseStudies = "",
  summary = false,
  options: PowerPointDesignOptions = {}
) {
  if (!summary) {
    const transportCandidateCount = options.semanticCandidates?.length ?? 0;
    trackEvent({
      name: "presentation_candidate_boundary_transport",
      feature: "proposal",
      status: "success",
      meta: {
        semantic_candidates_state: options.semanticCandidates == null
          ? "OMITTED"
          : transportCandidateCount > 0 ? "NONEMPTY" : "EMPTY",
        candidate_count: transportCandidateCount
      }
    });
  }
  const response = await fetch(`${API_BASE_URL}/api/download-pptx`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({
      powerpoint_generation_data: data,
      win_probability: winProbability,
      project_brief: projectBrief,
      client_company_info: clientCompanyInfo,
      competitor_site_url: competitorSiteUrl,
      competitor_company_name: competitorCompanyName,
      estimated_page_count: estimatedPageCount,
      cms_required: cmsRequired,
      contact_form_required: contactFormRequired,
      special_function_required: specialFunctionRequired,
      seo_required: seoRequired,
      content_creation_required: contentCreationRequired,
      desired_launch_timing: desiredLaunchTiming,
      budget_range: budgetRange,
      own_service_info: ownServiceInfo,
      past_proposal_template: pastProposalTemplate,
      case_studies: caseStudies,
      summary,
      design_template: options.designTemplate,
      brand_settings: options.brandSettings,
      presentation_quality_state: options.qualityState,
      presentation_layout_decisions: options.layoutDecisions,
      ...(summary || !options.semanticCandidates ? {} : {
        semantic_candidates: { candidates: options.semanticCandidates },
        semantic_confirmation_state: options.semanticCandidates.map(({ id, semantic_type, review_state, value }) => ({ id, semantic_type, review_state, value }))
      })
    } satisfies DownloadPptxPayload)
  });

  if (!response.ok) {
    const friendlyMessage = await readPowerPointErrorMessage(response.clone(), response.status);
    if (friendlyMessage) {
      throw new Error(friendlyMessage);
    }

    let message = `PowerPointの生成に失敗しました。status=${response.status}`;

    try {
      const errorBody = (await response.json()) as { detail?: string };
      if (errorBody.detail) {
        message = `${message}: ${errorBody.detail}`;
      }
    } catch {
      message = `${message}: バックエンドからエラー詳細を取得できませんでした。`;
    }

    throw new Error(message);
  }

  const blob = await response.blob();
  const fallbackTitle = summary ? `${data.deck_title}_要約版` : data.deck_title;
  const filename = getDownloadFilename(response.headers.get("Content-Disposition"), fallbackTitle);
  const qualityReport = getQualityReport(response.headers.get("X-Presentation-Quality-Report"));
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
  return { filename, qualityReport };
}

type CustomerReadyBlockedDetail = {
  error_code?: string;
  status?: string;
  score?: number;
  reasons?: string[];
  blockers?: string[];
};

async function readPowerPointErrorMessage(response: Response, status: number): Promise<string | null> {
  try {
    const errorBody = (await response.json()) as { detail?: string | CustomerReadyBlockedDetail };
    const detail = errorBody.detail;
    if (!detail) return null;
    if (typeof detail === "string") {
      return `PowerPointの生成に失敗しました。status=${status}: ${detail}`;
    }
    if (detail.error_code === "CUSTOMER_READY_BLOCKED") {
      const blockerText = detail.blockers?.length ? ` 確認事項: ${detail.blockers.slice(0, 2).join(" / ")}` : "";
      const reasonText = detail.reasons?.length ? ` 理由: ${detail.reasons.slice(0, 2).join(" / ")}` : "";
      return `顧客提出チェックで停止しました。スコア ${detail.score ?? "-"}点。${blockerText || reasonText || "内容を確認してください。"}`;
    }
  } catch {
    return null;
  }
  return null;
}

function getDownloadFilename(contentDisposition: string | null, fallbackTitle: string) {
  const fallback = `${sanitizeFileName(fallbackTitle || "ready-crew-proposal")}.pptx`;
  if (!contentDisposition) {
    return fallback;
  }

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }

  const asciiMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
  return asciiMatch?.[1] ?? fallback;
}

function sanitizeFileName(value: string) {
  return value
    .replace(/[\\/:*?"<>|]/g, "-")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 80);
}

function getQualityReport(value: string | null): PresentationQualityDownloadReport | null {
  if (!value) return null;
  try {
    return JSON.parse(decodeURIComponent(value)) as PresentationQualityDownloadReport;
  } catch {
    return null;
  }
}
