"""Presentation review acceptance and revision regeneration.

Revision ID: 20260713_1910
Revises: 20260713_1900
Create Date: 2026-07-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260713_1910"
down_revision = "20260713_1900"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return column_name in {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def _add_column(table_name: str, column_name: str, column_type: sa.types.TypeEngine, default: str | None = None, nullable: bool = False) -> None:
    if _has_table(table_name) and not _has_column(table_name, column_name):
        kwargs: dict[str, object] = {"nullable": nullable}
        if default is not None:
            kwargs["server_default"] = default
        op.add_column(table_name, sa.Column(column_name, column_type, **kwargs))


def _index_names(table_name: str) -> set[str]:
    if not _has_table(table_name):
        return set()
    return {str(item["name"]) for item in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    _add_column("presentation_reviews", "actions_json", sa.Text(), "")
    _add_column("presentation_reviews", "outline_json", sa.Text(), "")
    _add_column("presentation_reviews", "unresolved_issue_count", sa.Integer(), "0")
    _add_column("presentation_reviews", "score_schema_version", sa.Text(), "19.1")

    _add_column("presentation_revisions", "status", sa.Text(), "draft")
    _add_column("presentation_revisions", "selected_actions_json", sa.Text(), "")
    _add_column("presentation_revisions", "outline_json", sa.Text(), "")
    _add_column("presentation_revisions", "diff_json", sa.Text(), "")
    _add_column("presentation_revisions", "editor_url", sa.Text(), "")
    _add_column("presentation_revisions", "player_url", sa.Text(), "")
    _add_column("presentation_revisions", "generation_error_type", sa.Text(), "")
    _add_column("presentation_revisions", "generated_at", sa.Text(), None, nullable=True)
    _add_column("presentation_revisions", "approved_by", sa.Integer(), None, nullable=True)
    _add_column("presentation_revisions", "approved_at", sa.Text(), None, nullable=True)

    _add_column("presentation_revision_history", "change_reason", sa.Text(), "")
    _add_column("presentation_revision_history", "before_summary", sa.Text(), "")
    _add_column("presentation_revision_history", "after_summary", sa.Text(), "")
    _add_column("presentation_revision_history", "field_name", sa.Text(), "")
    _add_column("presentation_revision_history", "human_action", sa.Text(), "")
    _add_column("presentation_revision_history", "action_id", sa.Text(), "")

    if "idx_presentation_revisions_scope_number_unique" not in _index_names("presentation_revisions"):
        op.create_index(
            "idx_presentation_revisions_scope_number_unique",
            "presentation_revisions",
            ["organization_id", "workspace_id", "project_id", "revision_number"],
            unique=True,
        )


def downgrade() -> None:
    if "idx_presentation_revisions_scope_number_unique" in _index_names("presentation_revisions"):
        op.drop_index("idx_presentation_revisions_scope_number_unique", table_name="presentation_revisions")
