"""Baseline schema for v1.0 RC1.

Revision ID: 20260711_1701
Revises:
Create Date: 2026-07-11
"""

from __future__ import annotations

from alembic import op

from app.db import _schema_statements

revision = "20260711_1701"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    for statement in _schema_statements():
        op.execute(statement)


def downgrade() -> None:
    raise RuntimeError("Baseline downgrade is intentionally disabled to avoid destructive data loss.")
