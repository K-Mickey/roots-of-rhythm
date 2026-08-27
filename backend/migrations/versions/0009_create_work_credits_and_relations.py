"""Create work credits and work relations.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-27
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from roots_of_rhythm.music_catalog.infrastructure.models import (
    EDITORIAL_STATUS_CHECK,
    EVIDENCE_STATUS_CHECK,
    WORK_CREDIT_ROLE_CHECK,
    WORK_RELATION_TYPE_CHECK,
)
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_64, TEXT_1024

revision: str = "0009"
down_revision: str | None = "0008"
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
        "work_credits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=TEXT_32), nullable=False),
        sa.Column("credited_as", sa.String(length=TEXT_64), nullable=True),
        sa.Column("provenance", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("editorial_status", sa.String(length=TEXT_32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_work_credits_editorial_status"),
        sa.CheckConstraint(WORK_CREDIT_ROLE_CHECK, name="ck_work_credits_role"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_work_credits_work_person_role",
        "work_credits",
        ["work_id", "person_id", "role"],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
    op.create_index("ix_work_credits_work_id", "work_credits", ["work_id"], unique=False)
    op.create_index("ix_work_credits_person_id", "work_credits", ["person_id"], unique=False)
    _create_updated_at_trigger("work_credits")

    op.create_table(
        "work_relations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_work_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_work_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation_type", sa.String(length=TEXT_32), nullable=False),
        sa.Column("provenance", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("evidence_status", sa.String(length=TEXT_32), server_default="unverified", nullable=False),
        sa.Column("editorial_status", sa.String(length=TEXT_32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_work_relations_editorial_status"),
        sa.CheckConstraint(EVIDENCE_STATUS_CHECK, name="ck_work_relations_evidence_status"),
        sa.CheckConstraint(WORK_RELATION_TYPE_CHECK, name="ck_work_relations_relation_type"),
        sa.CheckConstraint("source_work_id <> target_work_id", name="ck_work_relations_no_self_reference"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_work_relations_source_target_type",
        "work_relations",
        ["source_work_id", "target_work_id", "relation_type"],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
    op.create_index("ix_work_relations_source_work_id", "work_relations", ["source_work_id"], unique=False)
    op.create_index("ix_work_relations_target_work_id", "work_relations", ["target_work_id"], unique=False)
    _create_updated_at_trigger("work_relations")


def downgrade() -> None:
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_work_relations_set_updated_at ON work_relations"))
    op.drop_index("ix_work_relations_target_work_id", table_name="work_relations")
    op.drop_index("ix_work_relations_source_work_id", table_name="work_relations")
    op.drop_index("uq_work_relations_source_target_type", table_name="work_relations")
    op.drop_table("work_relations")
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_work_credits_set_updated_at ON work_credits"))
    op.drop_index("ix_work_credits_person_id", table_name="work_credits")
    op.drop_index("ix_work_credits_work_id", table_name="work_credits")
    op.drop_index("uq_work_credits_work_person_role", table_name="work_credits")
    op.drop_table("work_credits")
