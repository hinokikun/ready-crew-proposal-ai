from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RequestContext:
    user_id: int
    role: str
    organization_id: int
    workspace_id: int
    membership_role: str
    request_id: str = ""

    @property
    def is_system_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_organization_admin(self) -> bool:
        return self.is_system_admin or self.membership_role == "organization_admin" or self.role == "manager"

    @property
    def can_write(self) -> bool:
        return self.role in {"admin", "manager", "member"} and self.membership_role != "viewer"
