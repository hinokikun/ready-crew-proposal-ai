type LogLevel = "debug" | "info" | "warn" | "error" | "silent";

const levelPriority: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
  silent: 100
};

const configuredLevel = (process.env.NEXT_PUBLIC_LOG_LEVEL as LogLevel | undefined) ?? (process.env.NODE_ENV === "production" ? "warn" : "debug");

function canLog(level: LogLevel) {
  return levelPriority[level] >= levelPriority[configuredLevel];
}

function isSensitiveKey(key: string) {
  return /authorization|cookie|password|token|secret|api[_-]?key|database[_-]?url|project[_-]?brief|generated|input[_-]?text|output[_-]?text/i.test(key);
}

function sanitizeMeta(meta: unknown): unknown {
  if (!meta || typeof meta !== "object") return meta;
  if (Array.isArray(meta)) return meta.slice(0, 20).map(sanitizeMeta);
  const source = meta as Record<string, unknown>;
  return Object.fromEntries(
    Object.entries(source).map(([key, value]) => [key, isSensitiveKey(key) ? "[REDACTED]" : sanitizeMeta(value)])
  );
}

export const logger = {
  debug(message: string, meta?: unknown) {
    if (canLog("debug")) console.debug(message, sanitizeMeta(meta));
  },
  info(message: string, meta?: unknown) {
    if (canLog("info")) console.info(message, sanitizeMeta(meta));
  },
  warn(message: string, meta?: unknown) {
    if (canLog("warn")) console.warn(message, sanitizeMeta(meta));
  },
  error(message: string, meta?: unknown) {
    if (canLog("error")) console.error(message, sanitizeMeta(meta));
  }
};
