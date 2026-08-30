"""Create recordings, credits, and work usages.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from roots_of_rhythm.music_catalog.infrastructure.models import (
    BILLING_ROLE_CHECK,
    EDITORIAL_STATUS_CHECK,
    RECORDING_CONTRIBUTION_KIND_CHECK,
    RECORDING_CREDIT_TARGET_KIND_CHECK,
    RECORDING_WORK_USAGE_KIND_CHECK,
    TEMPORAL_PRECISION_CHECK,
)
from roots_of_rhythm.text_lengths import TEXT_16, TEXT_32, TEXT_64, TEXT_1024

revision: str = "0011"
down_revision: str | None = "0010"
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
        "recordings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=TEXT_64), nullable=False),
        sa.Column("period_start_year", sa.Integer(), nullable=True),
        sa.Column("period_start_precision", sa.String(length=TEXT_32), nullable=True),
        sa.Column("period_end_year", sa.Integer(), nullable=True),
        sa.Column("period_end_precision", sa.String(length=TEXT_32), nullable=True),
        sa.Column("description", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("isrc", sa.String(length=TEXT_16), nullable=True),
        sa.Column("editorial_status", sa.String(length=TEXT_32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_recordings_editorial_status"),
        sa.CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column="period_start_year",
                precision_column="period_start_precision",
            ),
            name="ck_recordings_period_start",
        ),
        sa.CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column="period_end_year",
                precision_column="period_end_precision",
            ),
            name="ck_recordings_period_end",
        ),
        sa.CheckConstraint(
            "period_start_year IS NULL OR period_end_year IS NULL OR period_start_year <= period_end_year",
            name="ck_recordings_period_order",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recordings_editorial_status", "recordings", ["editorial_status"])
    _create_updated_at_trigger("recordings")

    op.create_table(
        "recording_credits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recording_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_kind", sa.String(length=TEXT_32), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("billing_role", sa.String(length=TEXT_32), nullable=False),
        sa.Column("contribution_kind", sa.String(length=TEXT_32), nullable=True),
        sa.Column("instrument", sa.String(length=TEXT_64), nullable=True),
        sa.Column("credited_as", sa.String(length=TEXT_64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(RECORDING_CREDIT_TARGET_KIND_CHECK, name="ck_recording_credits_target_kind"),
        sa.CheckConstraint(BILLING_ROLE_CHECK, name="ck_recording_credits_billing_role"),
        sa.CheckConstraint(RECORDING_CONTRIBUTION_KIND_CHECK, name="ck_recording_credits_contribution_kind"),
        sa.ForeignKeyConstraint(["recording_id"], ["recordings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recording_credits_recording_id", "recording_credits", ["recording_id"])
    op.create_index("ix_recording_credits_target", "recording_credits", ["target_kind", "target_id"])
    _create_updated_at_trigger("recording_credits")

    op.create_table(
        "recording_work_usages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recording_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usage_kind", sa.String(length=TEXT_32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(RECORDING_WORK_USAGE_KIND_CHECK, name="ck_recording_work_usages_usage_kind"),
        sa.CheckConstraint("position IS NULL OR position > 0", name="ck_recording_work_usages_position"),
        sa.ForeignKeyConstraint(["recording_id"], ["recordings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["work_id"], ["musical_works.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_recording_work_usages_recording_work_kind",
        "recording_work_usages",
        ["recording_id", "work_id", "usage_kind"],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
    op.create_index("ix_recording_work_usages_recording_id", "recording_work_usages", ["recording_id"])
    op.create_index("ix_recording_work_usages_work_id", "recording_work_usages", ["work_id"])
    _create_updated_at_trigger("recording_work_usages")


def downgrade() -> None:
    for table_name in ("recording_work_usages", "recording_credits", "recordings"):
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS trg_{table_name}_set_updated_at ON {table_name}"))
    op.drop_table("recording_work_usages")
    op.drop_table("recording_credits")
    op.drop_table("recordings")
