"""Presentation review loop tables.

Revision ID: 20260713_1900
Revises: 20260713_1820
Create Date: 2026-07-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260713_1900"
down_revision = "20260713_1820"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _ensure_context_columns(table_name: str) -> None:
    if not _has_column(table_name, "organization_id"):
        op.add_column(table_name, sa.Column("organization_id", sa.Integer(), nullable=False, server_default="1"))
    if not _has_column(table_name, "workspace_id"):
        op.add_column(table_name, sa.Column("workspace_id", sa.Integer(), nullable=False, server_default="1"))
    op.get_bind().exec_driver_sql(f"UPDATE {table_name} SET organization_id = 1 WHERE organization_id IS NULL OR organization_id = 0")
    op.get_bind().exec_driver_sql(f"UPDATE {table_name} SET workspace_id = 1 WHERE workspace_id IS NULL OR workspace_id = 0")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "presentation_reviews" not in tables:
        op.create_table(
            "presentation_reviews",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Text(), nullable=False),
            sa.Column("project_name", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("average_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("scores_json", sa.Text(), nullable=False, server_default=""),
            sa.Column("issues_json", sa.Text(), nullable=False, server_default=""),
            sa.Column("improvements_json", sa.Text(), nullable=False, server_default=""),
            sa.Column("improvement_summary", sa.Text(), nullable=False, server_default=""),
            sa.Column("improvement_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("approved", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("beautiful_ai_presentation_id", sa.Text(), nullable=False, server_default=""),
            sa.Column("organization_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("workspace_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
    _ensure_context_columns("presentation_reviews")
    if "idx_presentation_reviews_project" not in {item["name"] for item in inspector.get_indexes("presentation_reviews")}:
        op.create_index("idx_presentation_reviews_project", "presentation_reviews", ["project_id", "updated_at"])
    if "idx_presentation_reviews_org_workspace" not in {item["name"] for item in inspector.get_indexes("presentation_reviews")}:
        op.create_index("idx_presentation_reviews_org_workspace", "presentation_reviews", ["organization_id", "workspace_id"])

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "presentation_revisions" not in tables:
        op.create_table(
            "presentation_revisions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Text(), nullable=False),
            sa.Column("review_id", sa.Integer(), nullable=True),
            sa.Column("revision_number", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("revision_label", sa.Text(), nullable=False, server_default=""),
            sa.Column("slide_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("added_slide_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("removed_slide_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("modified_slide_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("improvement_summary", sa.Text(), nullable=False, server_default=""),
            sa.Column("beautiful_ai_presentation_id", sa.Text(), nullable=False, server_default=""),
            sa.Column("approved", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("organization_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("workspace_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
    _ensure_context_columns("presentation_revisions")
    if "idx_presentation_revisions_project" not in {item["name"] for item in inspector.get_indexes("presentation_revisions")}:
        op.create_index("idx_presentation_revisions_project", "presentation_revisions", ["project_id", "revision_number"])
    if "idx_presentation_revisions_org_workspace" not in {item["name"] for item in inspector.get_indexes("presentation_revisions")}:
        op.create_index("idx_presentation_revisions_org_workspace", "presentation_revisions", ["organization_id", "workspace_id"])

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "presentation_revision_history" not in tables:
        op.create_table(
            "presentation_revision_history",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Text(), nullable=False),
            sa.Column("from_revision_id", sa.Integer(), nullable=True),
            sa.Column("to_revision_id", sa.Integer(), nullable=False),
            sa.Column("change_type", sa.Text(), nullable=False, server_default=""),
            sa.Column("change_summary", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("organization_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("workspace_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
    _ensure_context_columns("presentation_revision_history")
    if "idx_presentation_revision_history_project" not in {item["name"] for item in inspector.get_indexes("presentation_revision_history")}:
        op.create_index(
            "idx_presentation_revision_history_project",
            "presentation_revision_history",
            ["project_id", "to_revision_id"],
        )
    if "idx_presentation_revision_history_org_workspace" not in {
        item["name"] for item in inspector.get_indexes("presentation_revision_history")
    }:
        op.create_index(
            "idx_presentation_revision_history_org_workspace",
            "presentation_revision_history",
            ["organization_id", "workspace_id"],
        )


def downgrade() -> None:
    op.drop_index("idx_presentation_revision_history_org_workspace", table_name="presentation_revision_history")
    op.drop_index("idx_presentation_revision_history_project", table_name="presentation_revision_history")
    op.drop_table("presentation_revision_history")
    op.drop_index("idx_presentation_revisions_org_workspace", table_name="presentation_revisions")
    op.drop_index("idx_presentation_revisions_project", table_name="presentation_revisions")
    op.drop_table("presentation_revisions")
    op.drop_index("idx_presentation_reviews_org_workspace", table_name="presentation_reviews")
    op.drop_index("idx_presentation_reviews_project", table_name="presentation_reviews")
    op.drop_table("presentation_reviews")
