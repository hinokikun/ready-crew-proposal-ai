const DEFAULT_API_URL = "http://localhost:8000";
const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL;
const isProductionBuild = process.env.NODE_ENV === "production";

function normalizeApiUrl(value: string): string {
  return value.trim().replace(/\/+$/, "");
}

if (isProductionBuild && !configuredApiUrl?.trim()) {
  throw new Error("NEXT_PUBLIC_API_URL must be configured for production builds.");
}

export const API_BASE_URL = normalizeApiUrl(configuredApiUrl ?? DEFAULT_API_URL);

export const SALES_ASSISTANT_FRONTEND_ENABLED =
  (process.env.NEXT_PUBLIC_SALES_ASSISTANT_ENABLED ?? "false").toLowerCase() === "true";

export const PROPOSAL_EXPORT_FRONTEND_ENABLED =
  (process.env.NEXT_PUBLIC_PROPOSAL_EXPORT_ENABLED ?? "false").toLowerCase() === "true";
