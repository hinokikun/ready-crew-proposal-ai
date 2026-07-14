const USAGE_LOG_KEY = "ready-crew-usage-log-v1";
const MAX_USAGE_LOG_COUNT = 100;
const AUTH_USER_KEY = "ready-crew-auth-user-v1";

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

export function buildScopedStorageKey(baseKey: string): string {
  if (typeof window === "undefined") return baseKey;
  try {
    const user = JSON.parse(window.localStorage.getItem(AUTH_USER_KEY) ?? "null") as {
      id?: number;
      current_organization_id?: number;
      current_workspace_id?: number;
    } | null;
    if (!user?.id) return baseKey;
    const organizationId = user.current_organization_id ?? "org";
    const workspaceId = user.current_workspace_id ?? "ws";
    return `${baseKey}:u${user.id}:o${organizationId}:w${workspaceId}`;
  } catch {
    return baseKey;
  }
}

export function readUsageLogs(): UsageLogEntry[] {
  return readCollection<UsageLogEntry>(buildScopedStorageKey(USAGE_LOG_KEY));
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
  writeCollection(buildScopedStorageKey(USAGE_LOG_KEY), next);
}

export const storageRepository = {
  readProjects: () => readCollection<StoredProject>(buildScopedStorageKey("ready-crew-projects-v1")),
  saveProjects: (items: StoredProject[]) => writeCollection(buildScopedStorageKey("ready-crew-projects-v1"), items),
  readCustomers: () => readCollection<StoredCustomer>(buildScopedStorageKey("ready-crew-customers-v1")),
  saveCustomers: (items: StoredCustomer[]) => writeCollection(buildScopedStorageKey("ready-crew-customers-v1"), items),
  readProposals: () => readCollection<StoredProposal>(buildScopedStorageKey("ready-crew-proposals-v1")),
  saveProposals: (items: StoredProposal[]) => writeCollection(buildScopedStorageKey("ready-crew-proposals-v1"), items),
  readMeetingMemos: () => readCollection<StoredMeetingMemo>(buildScopedStorageKey("ready-crew-meeting-memos-v1")),
  saveMeetingMemos: (items: StoredMeetingMemo[]) => writeCollection(buildScopedStorageKey("ready-crew-meeting-memos-v1"), items),
  readUsageLogs,
  appendUsageLog
};
