import { getAuthHeaders } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";
import { logger } from "@/lib/logger";

type ErrorBody = {
  detail?: string | { message?: string; error_type?: string; request_id?: string };
  message?: string;
  error_type?: string;
  request_id?: string;
};

export async function fetchJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...(init.headers ?? {})
    }
  });

  if (!response.ok) {
    const requestId = response.headers.get("x-request-id") ?? "";
    const message = await readApiError(response, "API request failed", requestId);
    logger.warn("API request failed", { path, status: response.status, requestId });
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function fetchBlob(path: string, init: RequestInit = {}): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...getAuthHeaders(),
      ...(init.headers ?? {})
    }
  });

  if (!response.ok) {
    const requestId = response.headers.get("x-request-id") ?? "";
    const message = await readApiError(response, "File download failed", requestId);
    logger.warn("File download failed", { path, status: response.status, requestId });
    throw new Error(message);
  }

  return response.blob();
}

async function readApiError(response: Response, fallback: string, requestId: string) {
  const requestHint = requestId ? ` request_id=${requestId}` : "";
  try {
    const errorBody = (await response.json()) as ErrorBody;
    const detailMessage =
      typeof errorBody.detail === "string"
        ? errorBody.detail
        : errorBody.detail?.message;
    const message = errorBody.message || detailMessage;
    const apiRequestId = errorBody.request_id || (typeof errorBody.detail === "object" ? errorBody.detail?.request_id : "") || requestId;
    const finalRequestHint = apiRequestId ? ` request_id=${apiRequestId}` : requestHint;
    return message
      ? `${fallback}: ${message}${finalRequestHint}`
      : `${fallback}: status=${response.status}${finalRequestHint}`;
  } catch {
    return `${fallback}: status=${response.status}${requestHint}`;
  }
}
