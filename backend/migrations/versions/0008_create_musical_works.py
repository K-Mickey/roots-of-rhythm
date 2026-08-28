"""Create musical works.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-27
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from roots_of_rhythm.music_catalog.infrastructure.models import (
    EDITORIAL_STATUS_CHECK,
    PERIOD_END_PRECISION_COLUMN,
    PERIOD_END_YEAR_COLUMN,
    PERIOD_START_PRECISION_COLUMN,
    PERIOD_START_YEAR_COLUMN,
    TEMPORAL_PRECISION_CHECK,
)
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_64, TEXT_1024

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def _create_updated_at_trigger(table_name: str) -> None:
    op.execute(
        sa.text(
            f"""
            CREATE TRIGGER trg_{table_name}_set_updated_at
            BEFORE UPDATE ON {table_name}
            FOR EACH ROW
            EXECUTE FUNCTION set_updated_at();
            """
        )
    )


def upgrade() -> None:
    op.create_table(
        "musical_works",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("editorial_status", sa.String(length=TEXT_32), nullable=False),
        sa.Column("canonical_title", sa.String(length=TEXT_64), nullable=False),
        sa.Column(
            "aliases",
            postgresql.ARRAY(sa.String(length=TEXT_64)),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("description", sa.String(length=TEXT_1024), nullable=True),
        sa.Column(PERIOD_START_YEAR_COLUMN, sa.Integer(), nullable=True),
        sa.Column(PERIOD_START_PRECISION_COLUMN, sa.String(length=TEXT_32), nullable=True),
        sa.Column(PERIOD_END_YEAR_COLUMN, sa.Integer(), nullable=True),
        sa.Column(PERIOD_END_PRECISION_COLUMN, sa.String(length=TEXT_32), nullable=True),
        sa.Column(
            "external_identities",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column("provenance", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_musical_works_editorial_status"),
        sa.CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_START_YEAR_COLUMN,
                precision_column=PERIOD_START_PRECISION_COLUMN,
            ),
            name="ck_musical_works_period_start",
        ),
        sa.CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_END_YEAR_COLUMN,
                precision_column=PERIOD_END_PRECISION_COLUMN,
            ),
            name="ck_musical_works_period_end",
        ),
        sa.CheckConstraint(
            "period_start_year IS NULL OR period_end_year IS NULL OR period_start_year <= period_end_year",
            name="ck_musical_works_period_order",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_musical_works_editorial_status", "musical_works", ["editorial_status"], unique=False)
    _create_updated_at_trigger("musical_works")


def downgrade() -> None:
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_musical_works_set_updated_at ON musical_works"))
    op.drop_index("ix_musical_works_editorial_status", table_name="musical_works")
    op.drop_table("musical_works")
