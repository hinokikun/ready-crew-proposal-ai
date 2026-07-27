"""Training metrics and business improvement reports.

Revision ID: 20260722_2500
Revises: 20260715_2400
Create Date: 2026-07-22
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260722_2500"
down_revision = "20260715_2400"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _column_names(table_name: str) -> set[str]:
    if not _has_table(table_name):
        return set()
    return {str(item["name"]) for item in sa.inspect(op.get_bind()).get_columns(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if column.name not in _column_names(table_name):
        op.add_column(table_name, column)


def upgrade() -> None:
    if _has_table("proposal_histories"):
        _add_column_if_missing("proposal_histories", sa.Column("project_name", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_histories", sa.Column("proposal_generation_duration_ms", sa.Integer(), nullable=False, server_default="0"))
        _add_column_if_missing("proposal_histories", sa.Column("powerpoint_generation_duration_ms", sa.Integer(), nullable=False, server_default="0"))
        _add_column_if_missing("proposal_histories", sa.Column("beautiful_ai_generation_duration_ms", sa.Integer(), nullable=False, server_default="0"))
        _add_column_if_missing("proposal_histories", sa.Column("pdf_generation_duration_ms", sa.Integer(), nullable=False, server_default="0"))
        _add_column_if_missing("proposal_histories", sa.Column("total_generation_duration_ms", sa.Integer(), nullable=False, server_default="0"))

    if not _has_table("business_improvement_reports"):
        op.create_table(
            "business_improvement_reports",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("project_id", sa.Integer(), nullable=True),
            sa.Column("project_name", sa.Text(), nullable=False, server_default=""),
            sa.Column("before_minutes", sa.Float(), nullable=False, server_default="0"),
            sa.Column("after_minutes", sa.Float(), nullable=False, server_default="0"),
            sa.Column("revision_minutes", sa.Float(), nullable=False, server_default="0"),
            sa.Column("review_minutes", sa.Float(), nullable=False, server_default="0"),
            sa.Column("total_after_minutes", sa.Float(), nullable=False, server_default="0"),
            sa.Column("saved_minutes", sa.Float(), nullable=False, server_default="0"),
            sa.Column("reduction_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("quality_score", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("mistake_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("comment", sa.Text(), nullable=False, server_default=""),
            sa.Column("organization_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("workspace_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )


def downgrade() -> None:
    # Keep collected training metrics to avoid losing user-entered UAT evidence.
    pass
