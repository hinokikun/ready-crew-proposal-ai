import { fetchJson } from "@/api/client";
import type { DailyBriefingData } from "@/types/app";

export function getTodayBriefing(): Promise<{ briefing: DailyBriefingData }> {
  return fetchJson("/api/briefing/today");
}

export function saveBriefingEvent(payload: {
  session_id: string;
  event_type: "viewed" | "priority_clicked" | "item_completed";
  project_id?: number;
  item_key?: string;
}): Promise<{ ok: boolean }> {
  return fetchJson("/api/briefing/events", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
