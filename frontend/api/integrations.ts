import { fetchJson } from "@/api/client";
import type {
  ConnectorReadinessItem,
  DryRunLog,
  ExternalIntakeCandidate,
  ExternalIntakeSourceType,
  IntegrationDryRunResult,
  IntegrationDryRunTemplate,
  IntegrationSetting,
  IntegrationStatus
} from "@/types/app";
import type { UserRole } from "@/types/app";

export type IntegrationSettingPayload = {
  status: IntegrationStatus;
  display_name?: string;
  enabled?: boolean;
  error_message?: string;
  allowed_roles?: UserRole[];
  requires_admin_approval?: boolean;
  data_retention_days?: number;
  security_note?: string;
};

export type ExternalIntakePayload = {
  source_provider: string;
  source_type: ExternalIntakeSourceType;
  title?: string;
  summary?: string;
  received_at?: string;
  metadata?: Record<string, string | number | boolean | null>;
};

export function getIntegrationSettings(): Promise<{ settings: IntegrationSetting[] }> {
  return fetchJson("/api/integrations/settings");
}

export function updateIntegrationSetting(
  provider: string,
  payload: IntegrationSettingPayload
): Promise<{ setting: IntegrationSetting }> {
  return fetchJson(`/api/integrations/settings/${encodeURIComponent(provider)}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function createExternalIntake(payload: ExternalIntakePayload): Promise<{ candidate: ExternalIntakeCandidate }> {
  return fetchJson("/api/integrations/intake", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getExternalIntakeCandidates(): Promise<{ candidates: ExternalIntakeCandidate[] }> {
  return fetchJson("/api/integrations/candidates");
}

export function runIntegrationDryRun(payload: {
  provider: "gmail" | "outlook" | "slack" | "teams" | "google_calendar" | "google_drive";
  template_type: IntegrationDryRunTemplate;
}): Promise<{ candidate: ExternalIntakeCandidate; dry_run: IntegrationDryRunResult }> {
  return fetchJson("/api/integrations/dry-run", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getIntegrationDryRunLogs(): Promise<{ logs: DryRunLog[] }> {
  return fetchJson("/api/integrations/dry-run/logs");
}

export function getConnectorReadiness(): Promise<{ readiness: ConnectorReadinessItem[] }> {
  return fetchJson("/api/integrations/readiness");
}

export function reviewExternalIntakeCandidate(
  itemId: number,
  payload: { status: "approved" | "rejected" | "archived"; review_comment?: string }
): Promise<{ candidate: ExternalIntakeCandidate }> {
  return fetchJson(`/api/integrations/candidates/${itemId}/review`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function convertExternalIntakeCandidate(itemId: number): Promise<{ candidate: ExternalIntakeCandidate }> {
  return fetchJson(`/api/integrations/candidates/${itemId}/convert`, {
    method: "POST"
  });
}
