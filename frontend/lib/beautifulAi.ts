import { fetchJson } from "@/client-api/client";
import { getAuthHeaders } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";
import type { PowerPointData, ProposalRequest, WinProbability } from "@/types/proposal";

export type BeautifulAiStatus = {
  enabled: boolean;
  configured: boolean;
  mock: boolean;
  api_mode?: string;
  resolved_endpoint?: string;
  api_reachable?: boolean;
  route_found?: boolean;
  backend_version?: string;
  last_success_at?: string;
  last_error_type?: string;
  provider: string;
  message: string;
};

export type BeautifulAiStatusProbe = {
  status: BeautifulAiStatus | null;
  apiReachable: boolean;
  routeFound: boolean;
  httpStatus: number | null;
  message: string;
  checkedAt: string;
};

export type BeautifulAiHistoryRecord = {
  id: number;
  project_id: string;
  title: string;
  status: string;
  http_status: number;
  error_type: string;
  response_text: string;
  request_json_safe: string;
  endpoint: string;
  api_mode: string;
  theme_id: string;
  workspace_config_id: string;
  created_at: string;
  updated_at: string;
};

export type BeautifulAiDiagnostics = {
  enabled: boolean;
  configured: boolean;
  mock: boolean;
  api_mode: string;
  resolved_endpoint: string;
  workspace_id: string;
  theme_id: string;
  last_http_status: number;
  last_error_type: string;
  last_response_text: string;
  last_request_json_safe: string;
  last_run_at: string;
  history: BeautifulAiHistoryRecord[];
};

export type BeautifulAiConnectionTestResult = {
  ok: boolean;
  http_status: number;
  error_type: string;
  message: string;
  response_text: string;
  checked_at: string;
};

export type BackendHealthProbe = {
  reachable: boolean;
  httpStatus: number | null;
  appVersion: string;
  gitCommit: string;
  gitCommitShort: string;
  gitBranch: string;
  beautifulAiRouteRegistered: boolean | null;
  beautifulAiEnabled: boolean | null;
  beautifulAiMock: boolean | null;
  beautifulAiApiMode: string;
  beautifulAiResolvedEndpoint: string;
  message: string;
  checkedAt: string;
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

export async function getBeautifulAiDiagnostics() {
  return fetchJson<BeautifulAiDiagnostics>("/api/beautiful-ai/diagnostics");
}

export async function runBeautifulAiConnectionTest() {
  return fetchJson<BeautifulAiConnectionTestResult>("/api/beautiful-ai/diagnostics/test", {
    method: "POST",
    body: JSON.stringify({})
  });
}

export async function getBeautifulAiStatusProbe(): Promise<BeautifulAiStatusProbe> {
  const checkedAt = new Date().toLocaleString("ja-JP");
  try {
    const response = await fetch(`${API_BASE_URL}/api/beautiful-ai/status`, {
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      }
    });
    if (response.ok) {
      const status = (await response.json()) as BeautifulAiStatus;
      return {
        status,
        apiReachable: status.api_reachable ?? true,
        routeFound: status.route_found ?? true,
        httpStatus: response.status,
        message: status.message || "Beautiful.ai status APIに接続できました。",
        checkedAt
      };
    }
    return {
      status: null,
      apiReachable: false,
      routeFound: response.status !== 404,
      httpStatus: response.status,
      message: beautifulAiStatusErrorMessage(response.status),
      checkedAt
    };
  } catch {
    return {
      status: null,
      apiReachable: false,
      routeFound: false,
      httpStatus: null,
      message: "Beautiful.ai status APIへ接続できません。Backend URL、CORS、Renderの起動状態を確認してください。",
      checkedAt
    };
  }
}

export async function getBackendHealthProbe(): Promise<BackendHealthProbe> {
  const checkedAt = new Date().toLocaleString("ja-JP");
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
    if (!response.ok) {
      return {
        reachable: false,
        httpStatus: response.status,
        appVersion: "",
        gitCommit: "",
        gitCommitShort: "",
        gitBranch: "",
        beautifulAiRouteRegistered: null,
        beautifulAiEnabled: null,
        beautifulAiMock: null,
        beautifulAiApiMode: "",
        beautifulAiResolvedEndpoint: "",
        message: `Render /health が status=${response.status} を返しました。`,
        checkedAt
      };
    }
    const body = (await response.json()) as {
      app_version?: string;
      git?: { commit?: string; commit_short?: string; branch?: string };
      routes?: { beautiful_ai_status_registered?: boolean };
      beautiful_ai?: { enabled?: boolean; mock?: boolean; route_registered?: boolean; api_mode?: string; resolved_endpoint?: string };
    };
    const routeRegistered = body.beautiful_ai?.route_registered ?? body.routes?.beautiful_ai_status_registered ?? null;
    return {
      reachable: true,
      httpStatus: response.status,
      appVersion: body.app_version || "",
      gitCommit: body.git?.commit || "",
      gitCommitShort: body.git?.commit_short || (body.git?.commit || "").slice(0, 7),
      gitBranch: body.git?.branch || "",
      beautifulAiRouteRegistered: routeRegistered,
      beautifulAiEnabled: body.beautiful_ai?.enabled ?? null,
      beautifulAiMock: body.beautiful_ai?.mock ?? null,
      beautifulAiApiMode: body.beautiful_ai?.api_mode || "",
      beautifulAiResolvedEndpoint: body.beautiful_ai?.resolved_endpoint || "",
      message: "Render /health に接続できました。",
      checkedAt
    };
  } catch {
    return {
      reachable: false,
      httpStatus: null,
      appVersion: "",
      gitCommit: "",
      gitCommitShort: "",
      gitBranch: "",
      beautifulAiRouteRegistered: null,
      beautifulAiEnabled: null,
      beautifulAiMock: null,
      beautifulAiApiMode: "",
      beautifulAiResolvedEndpoint: "",
      message: "Render /health へ接続できません。Backend URLまたはRenderの起動状態を確認してください。",
      checkedAt
    };
  }
}

function beautifulAiStatusErrorMessage(status: number) {
  if (status === 404) {
    return "Beautiful.ai APIルートが見つかりません。Renderが最新コミットをデプロイしているか、/health の route_registered を確認してください。";
  }
  if (status === 401) {
    return "Beautiful.ai status APIの認証に失敗しました。ログイン期限切れの可能性があります。再ログインしてください。";
  }
  if (status === 403) {
    return "Beautiful.ai status APIを見る権限がありません。ログイン中の権限を確認してください。";
  }
  if (status >= 500) {
    return "Beautiful.ai status APIでBackendエラーが発生しました。Renderログを確認してください。";
  }
  return `Beautiful.ai status APIを確認できませんでした。status=${status}`;
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
