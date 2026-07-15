import { fetchJson } from "@/client-api/client";
import type { ManagedUser, UserRole } from "@/types/app";

export function listUsers(): Promise<{ users: ManagedUser[] }> {
  return fetchJson("/api/users");
}

export function createUser(payload: { email: string; password: string; role: UserRole; display_name?: string }): Promise<{ user: ManagedUser }> {
  return fetchJson("/api/users", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateUser(
  userId: number,
  payload: Partial<{
    display_name: string;
    role: UserRole;
    password: string;
    password_change_required: boolean;
    is_active: boolean;
    pilot_enabled: boolean;
    pilot_completed: boolean;
    pilot_note: string;
  }>
): Promise<{ user: ManagedUser }> {
  return fetchJson(`/api/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function updateUserActive(userId: number, isActive: boolean): Promise<{ user: ManagedUser }> {
  return updateUser(userId, { is_active: isActive });
}

export function updateUserPilot(
  userId: number,
  payload: { pilot_enabled?: boolean; pilot_completed?: boolean; pilot_note?: string }
): Promise<{ user: ManagedUser }> {
  return updateUser(userId, payload);
}

export function deleteUser(userId: number): Promise<{ user: ManagedUser }> {
  return fetchJson(`/api/users/${userId}`, {
    method: "DELETE"
  });
}

export function changeOwnPassword(payload: {
  current_password: string;
  new_password: string;
  new_password_confirm: string;
}): Promise<{ ok: boolean; message: string; user: ManagedUser }> {
  return fetchJson("/api/users/me/password", {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}
