const DEFAULT_API_URL = "http://localhost:8000";

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  DEFAULT_API_URL
).replace(/\/+$/, "");

export const SALES_ASSISTANT_FRONTEND_ENABLED =
  (process.env.NEXT_PUBLIC_SALES_ASSISTANT_ENABLED ?? "false").toLowerCase() === "true";

export const PROPOSAL_EXPORT_FRONTEND_ENABLED =
  (process.env.NEXT_PUBLIC_PROPOSAL_EXPORT_ENABLED ?? "false").toLowerCase() === "true";
