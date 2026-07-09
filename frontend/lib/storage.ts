const USAGE_LOG_KEY = "ready-crew-usage-log-v1";
const MAX_USAGE_LOG_COUNT = 100;

export type UsageLogEntry = {
  id: string;
  createdAt: string;
  featureName: string;
  inputLength: number;
  outputType: string;
  status: "success" | "failure";
  errorType: string;
};

export function readUsageLogs(): UsageLogEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const parsed = JSON.parse(window.localStorage.getItem(USAGE_LOG_KEY) ?? "[]") as UsageLogEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function appendUsageLog(entry: Omit<UsageLogEntry, "id" | "createdAt">) {
  if (typeof window === "undefined") return;
  const next: UsageLogEntry[] = [
    {
      ...entry,
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      createdAt: new Date().toISOString()
    },
    ...readUsageLogs()
  ].slice(0, MAX_USAGE_LOG_COUNT);
  window.localStorage.setItem(USAGE_LOG_KEY, JSON.stringify(next));
}
