import type { PowerPointData, ProposalRequest, WinProbability } from "@/types/proposal";
import { getAuthHeaders } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";

type DownloadEstimatePdfPayload = {
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
  hearing_result?: string;
  own_service_info?: string;
  past_proposal_template?: string;
  case_studies?: string;
};

export async function downloadEstimatePdf(data: PowerPointData, form: ProposalRequest, winProbability?: WinProbability) {
  const response = await fetch(`${API_BASE_URL}/api/download-estimate-pdf`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({
      powerpoint_generation_data: data,
      win_probability: winProbability,
      project_brief: form.project_brief,
      client_company_info: form.client_company_info,
      competitor_site_url: form.competitor_site_url,
      competitor_company_name: form.competitor_company_name,
      estimated_page_count: form.estimated_page_count,
      cms_required: form.cms_required,
      contact_form_required: form.contact_form_required,
      special_function_required: form.special_function_required,
      seo_required: form.seo_required,
      content_creation_required: form.content_creation_required,
      desired_launch_timing: form.desired_launch_timing,
      budget_range: form.budget_range,
      hearing_result: form.hearing_result,
      own_service_info: form.own_service_info,
      past_proposal_template: form.past_proposal_template,
      case_studies: form.case_studies
    } satisfies DownloadEstimatePdfPayload)
  });

  if (!response.ok) {
    let message = `見積書PDFの生成に失敗しました。status=${response.status}`;

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
  const filename = getDownloadFilename(
    response.headers.get("Content-Disposition"),
    `${sanitizeFileName(extractClientName(data, form))}_概算見積書.pdf`
  );
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function extractClientName(data: PowerPointData, form: ProposalRequest) {
  if (data.client_name?.trim() && data.client_name !== "提案先企業") {
    return data.client_name.trim();
  }
  const firstLine = form.client_company_info
    .split(/\r?\n/)
    .map((line) => line.trim())
    .find(Boolean);
  return firstLine || "提案先企業";
}

function getDownloadFilename(contentDisposition: string | null, fallback: string) {
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
