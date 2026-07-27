"""Proposal Agent memory.

Revision ID: 20260722_5000
Revises: 20260722_2500
Create Date: 2026-07-22
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260722_5000"
down_revision = "20260722_2500"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _index_names(table_name: str) -> set[str]:
    if not _has_table(table_name):
        return set()
    return {str(item["name"]) for item in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    if not _has_table("proposal_agent_memories"):
        op.create_table(
            "proposal_agent_memories",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("project_id", sa.Integer(), nullable=True),
            sa.Column("project_name", sa.Text(), nullable=False, server_default=""),
            sa.Column("hearing_notes", sa.Text(), nullable=False, server_default=""),
            sa.Column("confirmation_items", sa.Text(), nullable=False, server_default=""),
            sa.Column("proposal_content", sa.Text(), nullable=False, server_default=""),
            sa.Column("competitor_analysis", sa.Text(), nullable=False, server_default=""),
            sa.Column("improvement_history", sa.Text(), nullable=False, server_default=""),
            sa.Column("organization_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("workspace_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
    indexes = _index_names("proposal_agent_memories")
    if "idx_proposal_agent_memories_org_workspace" not in indexes:
        op.create_index(
            "idx_proposal_agent_memories_org_workspace",
            "proposal_agent_memories",
            ["organization_id", "workspace_id"],
        )
    if "idx_proposal_agent_memories_project" not in indexes:
        op.create_index(
            "idx_proposal_agent_memories_project",
            "proposal_agent_memories",
            ["project_id", "updated_at"],
        )


def downgrade() -> None:
    # Keep Proposal Agent memories because they are user-entered sales context.
    pass
