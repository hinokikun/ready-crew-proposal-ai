from typing import Any


STORAGE_ROLES = {"admin", "manager", "member", "viewer"}
ADMIN_COMPAT_ROLES = {"admin", "manager"}
GENERAL_COMPAT_ROLES = {"member", "viewer"}


def normalize_role_for_storage(role: str) -> str:
    normalized = (role or "member").strip().lower()
    if normalized == "user":
        return "member"
    if normalized in STORAGE_ROLES:
        return normalized
    return "member"


def role_group(role: str) -> str:
    return "admin" if normalize_role_for_storage(role) in ADMIN_COMPAT_ROLES else "user"


def role_label(role: str) -> str:
    normalized = normalize_role_for_storage(role)
    if normalized == "admin":
        return "管理者"
    if normalized == "manager":
        return "管理者（互換）"
    if normalized == "viewer":
        return "一般利用者（閲覧のみ）"
    return "一般利用者"


def add_role_display_fields(user: dict[str, Any] | None) -> dict[str, Any] | None:
    if not user:
        return user
    user = dict(user)
    user["role_group"] = role_group(str(user.get("role", "")))
    user["role_label"] = role_label(str(user.get("role", "")))
    return user
