import { API_BASE_URL } from "@/lib/config";
import type { AuthUser, LoginMode, LoginResult } from "@/types/app";

export type { AuthUser, LoginMode, LoginResult } from "@/types/app";

const AUTH_TOKEN_KEY = "ready-crew-auth-token-v1";
const AUTH_USER_KEY = "ready-crew-auth-user-v1";
const LOGIN_MODE_KEY = "ready-crew-login-mode-v1";

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

export function saveAuthUser(user: AuthUser | undefined) {
  if (!user) return;
  window.localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function getStoredLoginMode(): LoginMode {
  if (typeof window === "undefined") return "user";
  const stored = window.localStorage.getItem(LOGIN_MODE_KEY);
  return stored === "admin" ? "admin" : "user";
}

export function saveLoginMode(mode: LoginMode) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(LOGIN_MODE_KEY, mode);
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(window.localStorage.getItem(AUTH_USER_KEY) ?? "null") as AuthUser | null;
  } catch {
    return null;
  }
}

export function clearAuthToken() {
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  window.localStorage.removeItem(AUTH_USER_KEY);
}

export async function logoutCurrentSession() {
  try {
    await fetch(`${API_BASE_URL}/api/auth/logout`, {
      method: "POST",
      headers: getAuthHeaders()
    });
  } catch {
    // Logout must continue even if the audit request cannot be delivered.
  } finally {
    clearAuthToken();
  }
}

export async function loginWithPassword(password: string, email = "", loginMode?: LoginMode): Promise<LoginResult> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(loginMode ? { email, password, login_mode: loginMode } : { email, password })
  });

  if (!response.ok) {
    const message = await readErrorMessage(response, "ログイン処理を完了できませんでした。");
    throw new Error(message);
  }

  const result = (await response.json()) as LoginResult;
  saveAuthToken(result.token);
  saveAuthUser(result.user);
  if (loginMode) saveLoginMode(loginMode);
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

  const status = (await response.json()) as { user?: AuthUser };
  saveAuthUser(status.user);
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
