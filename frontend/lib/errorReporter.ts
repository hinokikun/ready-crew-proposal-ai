import { logger } from "@/lib/logger";

const SENSITIVE_KEY_PATTERN = /authorization|cookie|password|token|secret|api[_-]?key|database_url|body|content|project_brief|generated/i;

function sanitizeValue(value: unknown): unknown {
  if (typeof value === "string") {
    return value.length > 240 ? `${value.slice(0, 240)}...` : value;
  }
  if (Array.isArray(value)) {
    return value.slice(0, 10).map(sanitizeValue);
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, entry]) => [
        key,
        SENSITIVE_KEY_PATTERN.test(key) ? "[REDACTED]" : sanitizeValue(entry)
      ])
    );
  }
  return value;
}

export function reportError(error: unknown, context: Record<string, unknown> = {}) {
  const message = error instanceof Error ? error.message : String(error ?? "Unknown error");
  logger.error("frontend_error", {
    message,
    context: sanitizeValue(context)
  });
}
