import { fetchJson } from "@/api/client";
import type { QualityGateRecord } from "@/types/app";

type QualityGateResponse = {
  ok?: boolean;
  gate: QualityGateRecord | null;
};

export function getQualityGate(projectId: string): Promise<QualityGateResponse> {
  return fetchJson(`/api/quality-gates/${encodeURIComponent(projectId)}`);
}

export function saveQualityGate(projectId: string, checklistItems: string[]): Promise<QualityGateResponse> {
  return fetchJson(`/api/quality-gates/${encodeURIComponent(projectId)}`, {
    method: "POST",
    body: JSON.stringify({ checklist_items: checklistItems })
  });
}

export function completeQualityGate(projectId: string, checklistItems: string[]): Promise<QualityGateResponse> {
  return fetchJson(`/api/quality-gates/${encodeURIComponent(projectId)}/complete`, {
    method: "PATCH",
    body: JSON.stringify({ checklist_items: checklistItems })
  });
}

export function bypassQualityGate(projectId: string, bypassReason: string): Promise<QualityGateResponse> {
  return fetchJson(`/api/quality-gates/${encodeURIComponent(projectId)}/bypass`, {
    method: "PATCH",
    body: JSON.stringify({ bypass_reason: bypassReason })
  });
}
