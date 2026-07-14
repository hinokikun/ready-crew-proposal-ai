"""Proposal optimization acceptance and evidence governance.

Revision ID: 20260713_2010
Revises: 20260713_2000
Create Date: 2026-07-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260713_2010"
down_revision = "20260713_2000"
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
    if _has_table("proposal_improvement_backlog"):
        _add_column_if_missing("proposal_improvement_backlog", sa.Column("evidence_type", sa.Text(), nullable=False, server_default="insufficient_data"))
        _add_column_if_missing("proposal_improvement_backlog", sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"))
        _add_column_if_missing("proposal_improvement_backlog", sa.Column("is_estimate", sa.Integer(), nullable=False, server_default="1"))
        _add_column_if_missing("proposal_improvement_backlog", sa.Column("calculation_method", sa.Text(), nullable=False, server_default="weighted_score_v20_1"))
        _add_column_if_missing("proposal_improvement_backlog", sa.Column("predicted_effect_json", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_improvement_backlog", sa.Column("measured_effect_json", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_improvement_backlog", sa.Column("measurement_status", sa.Text(), nullable=False, server_default="pending"))
        _add_column_if_missing("proposal_improvement_backlog", sa.Column("measured_at", sa.Text(), nullable=True))
        _add_column_if_missing("proposal_improvement_backlog", sa.Column("measurement_period", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_improvement_backlog", sa.Column("outcome_type", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_improvement_backlog", sa.Column("requires_human_review", sa.Integer(), nullable=False, server_default="1"))
        _add_column_if_missing("proposal_improvement_backlog", sa.Column("evidence_summary", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_improvement_backlog", sa.Column("evidence_period", sa.Text(), nullable=False, server_default=""))
        op.execute("UPDATE proposal_improvement_backlog SET status = 'suggested' WHERE status = 'open'")
        op.execute("UPDATE proposal_improvement_backlog SET status = 'selected' WHERE status = 'adopted'")
        op.execute("UPDATE proposal_improvement_backlog SET status = 'applied' WHERE status = 'done'")
        op.execute("UPDATE proposal_improvement_backlog SET status = 'archived' WHERE status = 'deferred'")

    if _has_table("proposal_best_practices"):
        _add_column_if_missing("proposal_best_practices", sa.Column("status", sa.Text(), nullable=False, server_default="pending_review"))
        _add_column_if_missing("proposal_best_practices", sa.Column("normalized_title", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_best_practices", sa.Column("tags", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_best_practices", sa.Column("structure_summary", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_best_practices", sa.Column("cta_type", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_best_practices", sa.Column("slide_order_pattern", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_best_practices", sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"))
        _add_column_if_missing("proposal_best_practices", sa.Column("evidence_period", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_best_practices", sa.Column("confidential_risk", sa.Text(), nullable=False, server_default="low"))
        _add_column_if_missing("proposal_best_practices", sa.Column("quality_score", sa.Integer(), nullable=False, server_default="50"))
        _add_column_if_missing("proposal_best_practices", sa.Column("has_prediction", sa.Integer(), nullable=False, server_default="0"))
        _add_column_if_missing("proposal_best_practices", sa.Column("approved_by", sa.Integer(), nullable=True))
        _add_column_if_missing("proposal_best_practices", sa.Column("approved_at", sa.Text(), nullable=True))
        _add_column_if_missing("proposal_best_practices", sa.Column("approval_reason", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_best_practices", sa.Column("rejection_reason", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_best_practices", sa.Column("archived_reason", sa.Text(), nullable=False, server_default=""))
        _add_column_if_missing("proposal_best_practices", sa.Column("merged_into_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    # Non-destructive downgrade: keep governance columns to avoid losing review evidence.
    pass
