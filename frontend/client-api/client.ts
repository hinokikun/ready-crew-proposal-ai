import { getAuthHeaders } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";
import { logger } from "@/lib/logger";

const DEFAULT_API_TIMEOUT_MS = 30000;

type ErrorBody = {
  detail?: string | { message?: string; error_type?: string; error_code?: string; request_id?: string };
  message?: string;
  error_type?: string;
  error_code?: string;
  request_id?: string;
};

export async function fetchJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const timeout = createTimeoutSignal(init.signal);
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: timeout.signal,
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
        ...(init.headers ?? {})
      }
    });
  } catch (caught) {
    if (caught instanceof DOMException && caught.name === "AbortError") {
      throw new Error("API request failed: 通信がタイムアウトしました。時間をおいて再試行してください。");
    }
    throw caught;
  } finally {
    timeout.dispose();
  }

  if (!response.ok) {
    const requestId = response.headers.get("x-request-id") ?? "";
    const message = await readApiError(response, "API request failed", requestId);
    logger.warn("API request failed", { path, status: response.status, requestId });
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function fetchBlob(path: string, init: RequestInit = {}): Promise<Blob> {
  const timeout = createTimeoutSignal(init.signal);
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: timeout.signal,
      headers: {
        ...getAuthHeaders(),
        ...(init.headers ?? {})
      }
    });
  } catch (caught) {
    if (caught instanceof DOMException && caught.name === "AbortError") {
      throw new Error("File download failed: 通信がタイムアウトしました。時間をおいて再試行してください。");
    }
    throw caught;
  } finally {
    timeout.dispose();
  }

  if (!response.ok) {
    const requestId = response.headers.get("x-request-id") ?? "";
    const message = await readApiError(response, "File download failed", requestId);
    logger.warn("File download failed", { path, status: response.status, requestId });
    throw new Error(message);
  }

  return response.blob();
}

function createTimeoutSignal(existingSignal?: AbortSignal | null): { signal?: AbortSignal; dispose: () => void } {
  if (existingSignal) {
    return { signal: existingSignal, dispose: () => undefined };
  }
  if (typeof AbortController === "undefined") {
    return { signal: undefined, dispose: () => undefined };
  }
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), DEFAULT_API_TIMEOUT_MS);
  return {
    signal: controller.signal,
    dispose: () => window.clearTimeout(timer)
  };
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
    const errorCode = errorBody.error_code || (typeof errorBody.detail === "object" ? errorBody.detail?.error_code : "") || "";
    const errorType = errorBody.error_type || (typeof errorBody.detail === "object" ? errorBody.detail?.error_type : "") || "";
    const apiRequestId = errorBody.request_id || (typeof errorBody.detail === "object" ? errorBody.detail?.request_id : "") || requestId;
    const finalRequestHint = apiRequestId ? ` request_id=${apiRequestId}` : requestHint;
    const codeHint = errorCode || errorType ? ` ${errorCode || errorType}` : "";
    return message
      ? `${fallback}: ${message}${codeHint}${finalRequestHint}`
      : `${fallback}: status=${response.status}${codeHint}${finalRequestHint}`;
  } catch {
    return `${fallback}: status=${response.status}${requestHint}`;
  }
}
