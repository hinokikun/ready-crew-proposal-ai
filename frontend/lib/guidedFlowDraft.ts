export const GUIDED_FLOW_DRAFT_VERSION = 1;
export const GUIDED_FLOW_DRAFT_TTL_MS = 7 * 24 * 60 * 60 * 1000;

export type GuidedFlowDraftScope = {
  userId: string | number;
  organizationId: string | number;
  workspaceId: string | number;
};

export type GuidedFlowDraft = {
  version: typeof GUIDED_FLOW_DRAFT_VERSION;
  savedAt: string;
  rawSourceText: string;
};

function normalizedScopeValue(value: string | number | null | undefined) {
  const normalized = String(value ?? "").trim();
  return normalized || null;
}

export function getGuidedFlowDraftKey(scope: Partial<GuidedFlowDraftScope> | null | undefined) {
  const userId = normalizedScopeValue(scope?.userId);
  const organizationId = normalizedScopeValue(scope?.organizationId);
  const workspaceId = normalizedScopeValue(scope?.workspaceId);
  if (!userId || !organizationId || !workspaceId) return null;
  return `ready-crew-guided-flow-draft-v1:u${userId}:o${organizationId}:w${workspaceId}`;
}

export function clearGuidedFlowDraft(scope: Partial<GuidedFlowDraftScope> | null | undefined) {
  const key = getGuidedFlowDraftKey(scope);
  if (!key || typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(key);
  } catch {
    // Storage may be unavailable; persistence is best effort.
  }
}

export function saveGuidedFlowDraft(
  scope: Partial<GuidedFlowDraftScope> | null | undefined,
  rawSourceText: string,
  now = Date.now()
) {
  const key = getGuidedFlowDraftKey(scope);
  if (!key || typeof window === "undefined") return false;
  try {
    window.localStorage.setItem(
      key,
      JSON.stringify({ version: GUIDED_FLOW_DRAFT_VERSION, savedAt: new Date(now).toISOString(), rawSourceText })
    );
    return true;
  } catch {
    return false;
  }
}

export function readGuidedFlowDraft(
  scope: Partial<GuidedFlowDraftScope> | null | undefined,
  now = Date.now()
) {
  const key = getGuidedFlowDraftKey(scope);
  if (!key || typeof window === "undefined") return null;
  let raw: string | null = null;
  try {
    raw = window.localStorage.getItem(key);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (
      !parsed ||
      typeof parsed !== "object" ||
      (parsed as GuidedFlowDraft).version !== GUIDED_FLOW_DRAFT_VERSION ||
      typeof (parsed as GuidedFlowDraft).savedAt !== "string" ||
      typeof (parsed as GuidedFlowDraft).rawSourceText !== "string" ||
      !(parsed as GuidedFlowDraft).rawSourceText.trim()
    ) {
      window.localStorage.removeItem(key);
      return null;
    }
    const savedAt = Date.parse((parsed as GuidedFlowDraft).savedAt);
    if (!Number.isFinite(savedAt) || now - savedAt > GUIDED_FLOW_DRAFT_TTL_MS) {
      window.localStorage.removeItem(key);
      return null;
    }
    return parsed as GuidedFlowDraft;
  } catch {
    if (raw !== null) {
      try {
        window.localStorage.removeItem(key);
      } catch {
        // Storage may be unavailable; persistence is best effort.
      }
    }
    return null;
  }
}
