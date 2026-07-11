import { fetchJson } from "@/api/client";
import type { PowerPointData, ProposalRequest, WinProbability } from "@/types/proposal";

export type BeautifulAiStatus = {
  enabled: boolean;
  configured: boolean;
  mock: boolean;
  provider: string;
  message: string;
};

export type BeautifulAiPresentation = {
  presentation_id: string;
  status: string;
  title: string;
  editor_url: string;
  player_url: string;
  created_at: string;
  provider: string;
  fallback_available: boolean;
};

export type BeautifulAiPresentationPayload = {
  project_id: string;
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
};

export async function getBeautifulAiStatus() {
  return fetchJson<BeautifulAiStatus>("/api/beautiful-ai/status");
}

export async function createBeautifulAiPresentation(payload: BeautifulAiPresentationPayload) {
  return fetchJson<BeautifulAiPresentation>("/api/beautiful-ai/presentations", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function recordBeautifulAiEditorOpened(presentationId: string) {
  if (!presentationId) return;
  await fetchJson<{ ok: boolean }>(`/api/beautiful-ai/presentations/${encodeURIComponent(presentationId)}/editor-opened`, {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function buildBeautifulAiPayload(
  projectId: string,
  data: PowerPointData,
  form: ProposalRequest,
  winProbability?: WinProbability
): BeautifulAiPresentationPayload {
  return {
    project_id: projectId,
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
    own_service_info: form.own_service_info,
    past_proposal_template: form.past_proposal_template,
    case_studies: form.case_studies
  };
}
