import type { PowerPointData, WinProbability } from "@/types/proposal";
import { API_BASE_URL } from "@/lib/config";

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
  caseStudies = ""
) {
  await downloadPowerPoint(
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
    false
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
  caseStudies = ""
) {
  await downloadPowerPoint(
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
    true
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
  summary = false
) {
  const response = await fetch(`${API_BASE_URL}/api/download-pptx`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
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
      summary
    } satisfies DownloadPptxPayload)
  });

  if (!response.ok) {
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
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
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
