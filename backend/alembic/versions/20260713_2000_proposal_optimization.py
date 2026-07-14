"""Proposal optimization engine tables.

Revision ID: 20260713_2000
Revises: 20260713_1910
Create Date: 2026-07-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260713_2000"
down_revision = "20260713_1910"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _index_names(table_name: str) -> set[str]:
    if not _has_table(table_name):
        return set()
    return {str(item["name"]) for item in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    if not _has_table("proposal_improvement_backlog"):
        op.create_table(
            "proposal_improvement_backlog",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Text(), nullable=False, server_default=""),
            sa.Column("category", sa.Text(), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False, server_default=""),
            sa.Column("priority", sa.Text(), nullable=False, server_default="Medium"),
            sa.Column("impact", sa.Float(), nullable=False, server_default="0"),
            sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
            sa.Column("expected_improvement", sa.Float(), nullable=False, server_default="0"),
            sa.Column("effort", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("importance", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("adoption_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("predicted_win_rate_delta", sa.Float(), nullable=False, server_default="0"),
            sa.Column("composite_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("status", sa.Text(), nullable=False, server_default="open"),
            sa.Column("owner", sa.Integer(), nullable=True),
            sa.Column("source_type", sa.Text(), nullable=False, server_default="optimization_engine"),
            sa.Column("explanation", sa.Text(), nullable=False, server_default=""),
            sa.Column("simulation_json", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("approved_by", sa.Integer(), nullable=True),
            sa.Column("approved_at", sa.Text(), nullable=True),
            sa.Column("organization_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("workspace_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
    if "idx_proposal_improvement_backlog_scope" not in _index_names("proposal_improvement_backlog"):
        op.create_index(
            "idx_proposal_improvement_backlog_scope",
            "proposal_improvement_backlog",
            ["organization_id", "workspace_id", "status", "composite_score"],
        )

    if not _has_table("proposal_best_practices"):
        op.create_table(
            "proposal_best_practices",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("category", sa.Text(), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("pattern_summary", sa.Text(), nullable=False, server_default=""),
            sa.Column("source_type", sa.Text(), nullable=False, server_default="learning"),
            sa.Column("success_metric", sa.Text(), nullable=False, server_default=""),
            sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
            sa.Column("adoption_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("organization_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("workspace_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
    if "idx_proposal_best_practices_scope" not in _index_names("proposal_best_practices"):
        op.create_index(
            "idx_proposal_best_practices_scope",
            "proposal_best_practices",
            ["organization_id", "workspace_id", "category", "confidence"],
        )


def downgrade() -> None:
    if "idx_proposal_best_practices_scope" in _index_names("proposal_best_practices"):
        op.drop_index("idx_proposal_best_practices_scope", table_name="proposal_best_practices")
    if "idx_proposal_improvement_backlog_scope" in _index_names("proposal_improvement_backlog"):
        op.drop_index("idx_proposal_improvement_backlog_scope", table_name="proposal_improvement_backlog")
