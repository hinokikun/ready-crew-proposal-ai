import { API_BASE_URL } from "@/lib/config";

const AUTH_TOKEN_KEY = "ready-crew-auth-token-v1";

export type LoginResult = {
  authenticated: boolean;
  token: string;
  expires_in_seconds: number;
  message: string;
};

export function getAuthToken() {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(AUTH_TOKEN_KEY) ?? "";
}

export function getAuthHeaders(): HeadersInit {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function saveAuthToken(token: string) {
  window.localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearAuthToken() {
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
}

export async function loginWithPassword(password: string): Promise<LoginResult> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ password })
  });

  if (!response.ok) {
    const message = await readErrorMessage(response, "ログインに失敗しました。");
    throw new Error(message);
  }

  const result = (await response.json()) as LoginResult;
  saveAuthToken(result.token);
  return result;
}

export async function verifyAuthToken(): Promise<boolean> {
  const token = getAuthToken();
  if (!token) return false;

  const response = await fetch(`${API_BASE_URL}/api/auth/status`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    clearAuthToken();
    return false;
  }

  return true;
}

async function readErrorMessage(response: Response, fallback: string) {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail || `${fallback} status=${response.status}`;
  } catch {
    return `${fallback} status=${response.status}`;
  }
}
