"""sessions: sandbox_id and task_id nullable until first run

Revision ID: a1b2c3d4e5f6
Revises: d2645c520e4b
Create Date: 2026-04-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "d2645c520e4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "sessions",
        "sandbox_id",
        existing_type=sa.String(length=255),
        nullable=True,
    )
    op.alter_column(
        "sessions",
        "task_id",
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "sessions",
        "sandbox_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "sessions",
        "task_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )
