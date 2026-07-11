from __future__ import annotations

from sqlite3 import Connection
from typing import Any

from app.prompts.repositories import (
    create_prompt_version,
    rollback_prompt_version,
    select_prompt_version_for_project,
    update_prompt_version_status,
)


class PromptVersionManager:
    def __init__(self, db: Connection):
        self.db = db

    def create(self, payload: dict[str, Any], *, user_id: int | None) -> dict[str, Any]:
        return create_prompt_version(
            self.db,
            prompt_name=payload["prompt_name"],
            version=payload["version"],
            description=payload.get("description", ""),
            target_agent=payload.get("target_agent", ""),
            prompt_template=payload["prompt_template"],
            status=payload.get("status", "draft"),
            user_id=user_id,
        )

    def set_status(self, *, version_id: int, status: str, user_id: int | None) -> dict[str, Any] | None:
        return update_prompt_version_status(self.db, version_id=version_id, status=status, user_id=user_id)

    def rollback(self, *, prompt_name: str, version: str, user_id: int | None) -> dict[str, Any] | None:
        return rollback_prompt_version(self.db, prompt_name=prompt_name, version=version, user_id=user_id)

    def route(self, *, prompt_name: str, project_id: int | None, user_id: int | None) -> dict[str, Any]:
        return select_prompt_version_for_project(self.db, prompt_name=prompt_name, project_id=project_id, user_id=user_id)
