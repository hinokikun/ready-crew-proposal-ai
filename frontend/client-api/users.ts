import { fetchJson } from "@/client-api/client";
import type { ManagedUser, UserRole } from "@/types/app";

export function listUsers(): Promise<{ users: ManagedUser[] }> {
  return fetchJson("/api/users");
}

export function createUser(payload: { email: string; password: string; role: UserRole }): Promise<{ user: ManagedUser }> {
  return fetchJson("/api/users", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateUserActive(userId: number, isActive: boolean): Promise<{ user: ManagedUser }> {
  return fetchJson(`/api/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive })
  });
}

export function updateUserPilot(
  userId: number,
  payload: { pilot_enabled?: boolean; pilot_completed?: boolean; pilot_note?: string }
): Promise<{ user: ManagedUser }> {
  return fetchJson(`/api/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}
