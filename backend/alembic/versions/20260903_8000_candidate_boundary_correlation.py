"""Add deterministic candidate-boundary correlation storage."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260903_8000"
down_revision = "20260722_7100"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return column_name in {str(column["name"]) for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    if not _has_table("analytics_events"):
        return
    if not _has_column("analytics_events", "candidate_boundary_correlation_id"):
        op.add_column("analytics_events", sa.Column("candidate_boundary_correlation_id", sa.String(length=64), nullable=True))
    op.create_index(
        "idx_analytics_events_candidate_boundary_correlation",
        "analytics_events",
        ["candidate_boundary_correlation_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    # Preserve diagnostic history and avoid destructive rollback.
    pass
