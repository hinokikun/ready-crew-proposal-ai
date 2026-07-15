"""Production user management and operations readiness.

Revision ID: 20260715_2400
Revises: 20260713_2010
Create Date: 2026-07-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260715_2400"
down_revision = "20260713_2010"
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
    if _has_table("users"):
        _add_column_if_missing("users", sa.Column("display_name", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("users", sa.Column("last_login_at", sa.Text(), nullable=True))
        _add_column_if_missing("users", sa.Column("password_change_required", sa.Integer(), nullable=False, server_default="0"))
        _add_column_if_missing("users", sa.Column("deleted_at", sa.Text(), nullable=True))
    if _has_table("audit_logs"):
        _add_column_if_missing("audit_logs", sa.Column("error_type", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("audit_logs", sa.Column("http_status", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    # Non-destructive downgrade: keep account safety columns to avoid losing audit context.
    pass
