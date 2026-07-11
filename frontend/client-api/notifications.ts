import { fetchJson } from "@/client-api/client";
import type { AiNotification, AiNotificationCenterData } from "@/types/app";

export function getAiNotifications(): Promise<AiNotificationCenterData> {
  return fetchJson("/api/notifications");
}

export function runAiWatchEngine(): Promise<AiNotificationCenterData> {
  return fetchJson("/api/notifications/run-watch", { method: "POST" });
}

export function markAiNotificationRead(notificationId: number): Promise<{ notification: AiNotification }> {
  return fetchJson(`/api/notifications/${notificationId}/read`, { method: "PATCH" });
}

export function markAiNotificationActioned(notificationId: number): Promise<{ notification: AiNotification }> {
  return fetchJson(`/api/notifications/${notificationId}/actioned`, { method: "PATCH" });
}

export function archiveAiNotification(notificationId: number): Promise<{ notification: AiNotification }> {
  return fetchJson(`/api/notifications/${notificationId}/archive`, { method: "PATCH" });
}
