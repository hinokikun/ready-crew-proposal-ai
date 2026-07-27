"""Training submission release candidate metrics.

Revision ID: 20260722_7100
Revises: 20260722_5000
Create Date: 2026-07-22
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260722_7100"
down_revision = "20260722_5000"
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
    if _has_table("business_improvement_reports"):
        _add_column_if_missing("business_improvement_reports", sa.Column("ai_input_minutes", sa.Float(), nullable=False, server_default="0"))
        _add_column_if_missing("business_improvement_reports", sa.Column("ai_wait_minutes", sa.Float(), nullable=False, server_default="0"))
        _add_column_if_missing("business_improvement_reports", sa.Column("is_demo", sa.Integer(), nullable=False, server_default="0"))
    if _has_table("proposal_histories"):
        _add_column_if_missing("proposal_histories", sa.Column("is_demo", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    # Keep user-entered training evidence. Column removal is intentionally not performed.
    pass
