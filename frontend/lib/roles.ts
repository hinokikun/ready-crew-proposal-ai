import type { UserRole } from "@/types/app";

export type CreatableUserRole = "admin" | "member" | "viewer";

export function normalizeDisplayRole(role?: UserRole | string): "admin" | "user" {
  return role === "admin" || role === "manager" || role === "system_admin" || role === "organization_admin" ? "admin" : "user";
}

export function getRoleLabel(role?: UserRole | string): string {
  if (role === "admin" || role === "system_admin") return "管理者";
  if (role === "manager" || role === "organization_admin") return "組織管理者";
  if (role === "viewer") return "閲覧者";
  return "一般利用者";
}

export function isAdminRole(role?: UserRole | string): boolean {
  return role === "admin";
}

export function isManagerCompatibleRole(role?: UserRole | string): boolean {
  return role === "admin" || role === "manager";
}

export function canUseWorkFeatures(role?: UserRole | string): boolean {
  return role === "admin" || role === "manager" || role === "member" || role === "user";
}

export function canViewOnly(role?: UserRole | string): boolean {
  return role === "viewer";
}
