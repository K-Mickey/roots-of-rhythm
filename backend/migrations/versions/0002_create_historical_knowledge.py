"""Create Historical Knowledge claims and sources.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-18
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from roots_of_rhythm.historical_knowledge.domain.value_objects import (
    LONG_TEXT_MAX_LENGTH,
    SHORT_TEXT_MAX_LENGTH,
    URL_MAX_LENGTH,
)
from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    EDITORIAL_STATUS_CHECK,
    EVIDENCE_ROLE_CHECK,
    EVIDENCE_STATUS_CHECK,
    FRAGMENT_REVIEW_CHECK,
    RELATION_TYPE_CHECK,
)

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=SHORT_TEXT_MAX_LENGTH), nullable=False),
        sa.Column("institution_name", sa.String(length=SHORT_TEXT_MAX_LENGTH), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "source_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=SHORT_TEXT_MAX_LENGTH), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "source_fragments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("locator_text", sa.String(length=LONG_TEXT_MAX_LENGTH), nullable=True),
        sa.Column("external_url", sa.String(length=URL_MAX_LENGTH), nullable=True),
        sa.CheckConstraint(FRAGMENT_REVIEW_CHECK, name="ck_source_fragments_review_status"),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "genre_relation_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_genre_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_genre_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation_type", sa.String(length=64), nullable=False),
        sa.Column("editorial_status", sa.String(length=32), nullable=False),
        sa.Column("evidence_status", sa.String(length=32), nullable=False),
        sa.Column("explanation", sa.String(length=LONG_TEXT_MAX_LENGTH), nullable=True),
        sa.Column("period_label", sa.String(length=SHORT_TEXT_MAX_LENGTH), nullable=True),
        sa.Column("period_start_year", sa.Integer(), nullable=True),
        sa.Column("period_start_precision", sa.String(length=32), nullable=True),
        sa.Column("period_end_year", sa.Integer(), nullable=True),
        sa.Column("period_end_precision", sa.String(length=32), nullable=True),
        sa.Column("geography_summary", sa.String(length=SHORT_TEXT_MAX_LENGTH), nullable=True),
        sa.Column("provenance_summary", sa.String(length=LONG_TEXT_MAX_LENGTH), nullable=True),
        sa.CheckConstraint(RELATION_TYPE_CHECK, name="ck_genre_relation_claims_relation_type"),
        sa.CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_genre_relation_claims_editorial_status"),
        sa.CheckConstraint(EVIDENCE_STATUS_CHECK, name="ck_genre_relation_claims_evidence_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "subject_genre_id",
            "target_genre_id",
            "relation_type",
            name="uq_genre_relation_claims_endpoints_type",
        ),
    )
    op.create_index("ix_genre_relation_claims_subject_genre_id", "genre_relation_claims", ["subject_genre_id"])
    op.create_index("ix_genre_relation_claims_target_genre_id", "genre_relation_claims", ["target_genre_id"])
    op.create_table(
        "claim_evidence_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_fragment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("locator_text", sa.String(length=LONG_TEXT_MAX_LENGTH), nullable=True),
        sa.Column("external_url", sa.String(length=URL_MAX_LENGTH), nullable=True),
        sa.CheckConstraint(EVIDENCE_ROLE_CHECK, name="ck_claim_evidence_references_role"),
        sa.ForeignKeyConstraint(["claim_id"], ["genre_relation_claims.id"]),
        sa.ForeignKeyConstraint(["source_fragment_id"], ["source_fragments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_claim_evidence_references_claim_id", "claim_evidence_references", ["claim_id"])


def downgrade() -> None:
    op.drop_index("ix_claim_evidence_references_claim_id", table_name="claim_evidence_references")
    op.drop_table("claim_evidence_references")
    op.drop_index("ix_genre_relation_claims_target_genre_id", table_name="genre_relation_claims")
    op.drop_index("ix_genre_relation_claims_subject_genre_id", table_name="genre_relation_claims")
    op.drop_table("genre_relation_claims")
    op.drop_table("source_fragments")
    op.drop_table("source_versions")
    op.drop_table("sources")
