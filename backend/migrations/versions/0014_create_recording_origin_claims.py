"""Create recording origin claims.

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-29
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    EDITORIAL_STATUS_CHECK,
    EVIDENCE_ROLE_CHECK,
    EVIDENCE_STATUS_CHECK,
    RECORDING_ORIGIN_PREDICATE_CHECK,
)
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_64, TEXT_1024, TEXT_2048

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "recording_origin_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recording_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("predicate", sa.String(length=TEXT_64), nullable=False),
        sa.Column("editorial_status", sa.String(length=TEXT_32), nullable=False),
        sa.Column("evidence_status", sa.String(length=TEXT_32), nullable=False),
        sa.Column("explanation", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("period_label", sa.String(length=TEXT_64), nullable=True),
        sa.Column("period_start_year", sa.Integer(), nullable=True),
        sa.Column("period_start_precision", sa.String(length=TEXT_32), nullable=True),
        sa.Column("period_end_year", sa.Integer(), nullable=True),
        sa.Column("period_end_precision", sa.String(length=TEXT_32), nullable=True),
        sa.Column("geography_summary", sa.String(length=TEXT_64), nullable=True),
        sa.Column("provenance_summary", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(RECORDING_ORIGIN_PREDICATE_CHECK, name="ck_recording_origin_claims_predicate"),
        sa.CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_recording_origin_claims_editorial_status"),
        sa.CheckConstraint(EVIDENCE_STATUS_CHECK, name="ck_recording_origin_claims_evidence_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_recording_origin_claims_endpoints_predicate",
        "recording_origin_claims",
        ["recording_id", "work_id", "predicate"],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
    op.create_index("ix_recording_origin_claims_recording_id", "recording_origin_claims", ["recording_id"])
    op.create_index("ix_recording_origin_claims_work_id", "recording_origin_claims", ["work_id"])

    op.create_table(
        "recording_origin_claim_evidence_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_fragment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=TEXT_32), nullable=False),
        sa.Column("locator_text", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("external_url", sa.String(length=TEXT_2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(
            EVIDENCE_ROLE_CHECK,
            name="ck_recording_origin_claim_evidence_references_role",
        ),
        sa.ForeignKeyConstraint(["claim_id"], ["recording_origin_claims.id"]),
        sa.ForeignKeyConstraint(["source_fragment_id"], ["source_fragments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recording_origin_claim_evidence_references_claim_id",
        "recording_origin_claim_evidence_references",
        ["claim_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recording_origin_claim_evidence_references_claim_id",
        table_name="recording_origin_claim_evidence_references",
    )
    op.drop_table("recording_origin_claim_evidence_references")
    op.drop_index("ix_recording_origin_claims_work_id", table_name="recording_origin_claims")
    op.drop_index("ix_recording_origin_claims_recording_id", table_name="recording_origin_claims")
    op.drop_index(
        "uq_recording_origin_claims_endpoints_predicate",
        table_name="recording_origin_claims",
        postgresql_where=sa.text("deleted = false"),
    )
    op.drop_table("recording_origin_claims")
