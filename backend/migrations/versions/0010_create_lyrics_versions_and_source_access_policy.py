"""Create lyrics versions and source access policy.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-27
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from roots_of_rhythm.historical_knowledge.domain.enums import SourceAccessPolicy
from roots_of_rhythm.historical_knowledge.infrastructure.models import SOURCE_ACCESS_POLICY_CHECK
from roots_of_rhythm.music_catalog.infrastructure.models import (
    EDITORIAL_STATUS_CHECK,
    LYRICS_CREATION_METHOD_CHECK,
    LYRICS_USAGE_KIND_CHECK,
    LYRICS_VERSION_RELATION_TYPE_CHECK,
    WORK_CREDIT_ROLE_CHECK,
)
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_64, TEXT_1024, TEXT_4096

revision: str = "0010"
down_revision: str | None = "0009"
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
    op.add_column(
        "sources",
        sa.Column(
            "access_policy",
            sa.String(length=TEXT_32),
            server_default=SourceAccessPolicy.WITHHOLD_PUBLIC_BODY.value,
            nullable=False,
        ),
    )
    op.create_check_constraint("ck_sources_access_policy", "sources", SOURCE_ACCESS_POLICY_CHECK)

    op.create_table(
        "lyrics_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language_tag", sa.String(length=TEXT_64), nullable=False),
        sa.Column("usage_kind", sa.String(length=TEXT_32), nullable=False),
        sa.Column("creation_method", sa.String(length=TEXT_32), nullable=False),
        sa.Column("label", sa.String(length=TEXT_64), nullable=True),
        sa.Column("body", sa.String(length=TEXT_4096), nullable=True),
        sa.Column("provenance", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("editorial_status", sa.String(length=TEXT_32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_lyrics_versions_editorial_status"),
        sa.CheckConstraint(LYRICS_USAGE_KIND_CHECK, name="ck_lyrics_versions_usage_kind"),
        sa.CheckConstraint(LYRICS_CREATION_METHOD_CHECK, name="ck_lyrics_versions_creation_method"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_lyrics_versions_work_language_usage_label",
        "lyrics_versions",
        ["work_id", "language_tag", "usage_kind", sa.text("COALESCE(label, '')")],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
    op.create_index("ix_lyrics_versions_work_id", "lyrics_versions", ["work_id"], unique=False)
    op.create_index(
        "ix_lyrics_versions_source_version_id",
        "lyrics_versions",
        ["source_version_id"],
        unique=False,
    )
    _create_updated_at_trigger("lyrics_versions")

    op.create_table(
        "lyrics_version_credits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lyrics_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=TEXT_32), nullable=False),
        sa.Column("credited_as", sa.String(length=TEXT_64), nullable=True),
        sa.Column("provenance", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("editorial_status", sa.String(length=TEXT_32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_lyrics_version_credits_editorial_status"),
        sa.CheckConstraint(WORK_CREDIT_ROLE_CHECK, name="ck_lyrics_version_credits_role"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_lyrics_version_credits_version_person_role",
        "lyrics_version_credits",
        ["lyrics_version_id", "person_id", "role"],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
    op.create_index(
        "ix_lyrics_version_credits_lyrics_version_id",
        "lyrics_version_credits",
        ["lyrics_version_id"],
        unique=False,
    )
    _create_updated_at_trigger("lyrics_version_credits")

    op.create_table(
        "lyrics_version_relations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_lyrics_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_lyrics_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation_type", sa.String(length=TEXT_32), nullable=False),
        sa.Column("provenance", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("editorial_status", sa.String(length=TEXT_32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_lyrics_version_relations_editorial_status"),
        sa.CheckConstraint(LYRICS_VERSION_RELATION_TYPE_CHECK, name="ck_lyrics_version_relations_relation_type"),
        sa.CheckConstraint(
            "source_lyrics_version_id <> target_lyrics_version_id",
            name="ck_lyrics_version_relations_no_self_reference",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_lyrics_version_relations_source_target_type",
        "lyrics_version_relations",
        ["source_lyrics_version_id", "target_lyrics_version_id", "relation_type"],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
    op.create_index(
        "ix_lyrics_version_relations_source",
        "lyrics_version_relations",
        ["source_lyrics_version_id"],
        unique=False,
    )
    op.create_index(
        "ix_lyrics_version_relations_target",
        "lyrics_version_relations",
        ["target_lyrics_version_id"],
        unique=False,
    )
    _create_updated_at_trigger("lyrics_version_relations")


def downgrade() -> None:
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_lyrics_version_relations_set_updated_at ON lyrics_version_relations")
    )
    op.drop_index("ix_lyrics_version_relations_target", table_name="lyrics_version_relations")
    op.drop_index("ix_lyrics_version_relations_source", table_name="lyrics_version_relations")
    op.drop_index("uq_lyrics_version_relations_source_target_type", table_name="lyrics_version_relations")
    op.drop_table("lyrics_version_relations")
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_lyrics_version_credits_set_updated_at ON lyrics_version_credits"))
    op.drop_index("ix_lyrics_version_credits_lyrics_version_id", table_name="lyrics_version_credits")
    op.drop_index("uq_lyrics_version_credits_version_person_role", table_name="lyrics_version_credits")
    op.drop_table("lyrics_version_credits")
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_lyrics_versions_set_updated_at ON lyrics_versions"))
    op.drop_index("ix_lyrics_versions_source_version_id", table_name="lyrics_versions")
    op.drop_index("ix_lyrics_versions_work_id", table_name="lyrics_versions")
    op.drop_index("uq_lyrics_versions_work_language_usage_label", table_name="lyrics_versions")
    op.drop_table("lyrics_versions")
    op.drop_constraint("ck_sources_access_policy", "sources", type_="check")
    op.drop_column("sources", "access_policy")
