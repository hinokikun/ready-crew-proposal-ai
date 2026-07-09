const USAGE_LOG_KEY = "ready-crew-usage-log-v1";
const MAX_USAGE_LOG_COUNT = 100;

export type StoredProject = {
  id: string;
  createdAt: string;
  title: string;
  status: "draft" | "proposed" | "archived";
};

export type StoredCustomer = {
  id: string;
  createdAt: string;
  displayName: string;
  note: string;
};

export type StoredProposal = {
  id: string;
  createdAt: string;
  projectId: string;
  outputTypes: string[];
};

export type StoredMeetingMemo = {
  id: string;
  createdAt: string;
  projectId: string;
  summary: string;
};

export type UsageLogEntry = {
  id: string;
  createdAt: string;
  featureName: string;
  inputLength: number;
  outputType: string;
  status: "success" | "failure";
  errorType: string;
};

function readCollection<T>(key: string): T[] {
  if (typeof window === "undefined") return [];
  try {
    const parsed = JSON.parse(window.localStorage.getItem(key) ?? "[]") as T[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeCollection<T>(key: string, items: T[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(key, JSON.stringify(items));
}

export function readUsageLogs(): UsageLogEntry[] {
  return readCollection<UsageLogEntry>(USAGE_LOG_KEY);
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
  writeCollection(USAGE_LOG_KEY, next);
}

export const storageRepository = {
  readProjects: () => readCollection<StoredProject>("ready-crew-projects-v1"),
  saveProjects: (items: StoredProject[]) => writeCollection("ready-crew-projects-v1", items),
  readCustomers: () => readCollection<StoredCustomer>("ready-crew-customers-v1"),
  saveCustomers: (items: StoredCustomer[]) => writeCollection("ready-crew-customers-v1", items),
  readProposals: () => readCollection<StoredProposal>("ready-crew-proposals-v1"),
  saveProposals: (items: StoredProposal[]) => writeCollection("ready-crew-proposals-v1", items),
  readMeetingMemos: () => readCollection<StoredMeetingMemo>("ready-crew-meeting-memos-v1"),
  saveMeetingMemos: (items: StoredMeetingMemo[]) => writeCollection("ready-crew-meeting-memos-v1", items),
  readUsageLogs,
  appendUsageLog
};
