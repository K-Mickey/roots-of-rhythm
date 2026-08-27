"""Create groups and group memberships.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-25
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

revision: str = "0007"
down_revision: str | None = "0006"
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
        "groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("editorial_status", sa.String(length=TEXT_32), nullable=False),
        sa.Column("canonical_name", sa.String(length=TEXT_64), nullable=False),
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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_groups_editorial_status"),
        sa.CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_START_YEAR_COLUMN,
                precision_column=PERIOD_START_PRECISION_COLUMN,
            ),
            name="ck_groups_period_start",
        ),
        sa.CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_END_YEAR_COLUMN,
                precision_column=PERIOD_END_PRECISION_COLUMN,
            ),
            name="ck_groups_period_end",
        ),
        sa.CheckConstraint(
            "period_start_year IS NULL OR period_end_year IS NULL OR period_start_year <= period_end_year",
            name="ck_groups_period_order",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_groups_editorial_status", "groups", ["editorial_status"], unique=False)
    _create_updated_at_trigger("groups")

    op.create_table(
        "group_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("editorial_status", sa.String(length=TEXT_32), nullable=False),
        sa.Column(PERIOD_START_YEAR_COLUMN, sa.Integer(), nullable=True),
        sa.Column(PERIOD_START_PRECISION_COLUMN, sa.String(length=TEXT_32), nullable=True),
        sa.Column(PERIOD_END_YEAR_COLUMN, sa.Integer(), nullable=True),
        sa.Column(PERIOD_END_PRECISION_COLUMN, sa.String(length=TEXT_32), nullable=True),
        sa.Column(
            "roles_or_instruments",
            postgresql.ARRAY(sa.String(length=TEXT_64)),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("provenance", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_group_memberships_editorial_status"),
        sa.CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_START_YEAR_COLUMN,
                precision_column=PERIOD_START_PRECISION_COLUMN,
            ),
            name="ck_group_memberships_period_start",
        ),
        sa.CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_END_YEAR_COLUMN,
                precision_column=PERIOD_END_PRECISION_COLUMN,
            ),
            name="ck_group_memberships_period_end",
        ),
        sa.CheckConstraint(
            "period_start_year IS NULL OR period_end_year IS NULL OR period_start_year <= period_end_year",
            name="ck_group_memberships_period_order",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_group_memberships_group_id", "group_memberships", ["group_id"], unique=False)
    op.create_index("ix_group_memberships_person_id", "group_memberships", ["person_id"], unique=False)
    _create_updated_at_trigger("group_memberships")


def downgrade() -> None:
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_group_memberships_set_updated_at ON group_memberships"))
    op.drop_index("ix_group_memberships_person_id", table_name="group_memberships")
    op.drop_index("ix_group_memberships_group_id", table_name="group_memberships")
    op.drop_table("group_memberships")
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_groups_set_updated_at ON groups"))
    op.drop_index("ix_groups_editorial_status", table_name="groups")
    op.drop_table("groups")
