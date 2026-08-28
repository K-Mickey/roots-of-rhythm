"""Expand person and classification assignment content.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from roots_of_rhythm.music_catalog.domain.enums import EvidenceStatus
from roots_of_rhythm.music_catalog.infrastructure.models import EVIDENCE_STATUS_CHECK
from roots_of_rhythm.people_catalog.infrastructure.models import (
    PERSON_NAME_UNIQUE_CONSTRAINT,
    TEMPORAL_PRECISION_CHECK,
)
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_1024

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.drop_index(PERSON_NAME_UNIQUE_CONSTRAINT, table_name="persons")
    op.add_column(
        "persons",
        sa.Column(
            "aliases",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column("persons", sa.Column("birth_year", sa.Integer(), nullable=True))
    op.add_column("persons", sa.Column("birth_precision", sa.String(length=TEXT_32), nullable=True))
    op.add_column("persons", sa.Column("death_year", sa.Integer(), nullable=True))
    op.add_column("persons", sa.Column("death_precision", sa.String(length=TEXT_32), nullable=True))
    op.add_column(
        "persons",
        sa.Column(
            "external_identities",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_persons_birth_date",
        "persons",
        TEMPORAL_PRECISION_CHECK.format(year_column="birth_year", precision_column="birth_precision"),
    )
    op.create_check_constraint(
        "ck_persons_death_date",
        "persons",
        TEMPORAL_PRECISION_CHECK.format(year_column="death_year", precision_column="death_precision"),
    )
    op.create_check_constraint(
        "ck_persons_birth_before_death",
        "persons",
        "birth_year IS NULL OR death_year IS NULL OR birth_year <= death_year",
    )

    op.add_column(
        "classification_assignments",
        sa.Column("explanation", sa.String(length=TEXT_1024), nullable=True),
    )
    op.add_column(
        "classification_assignments",
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "classification_assignments",
        sa.Column("provenance", sa.String(length=TEXT_1024), nullable=True),
    )
    op.add_column(
        "classification_assignments",
        sa.Column(
            "evidence_status",
            sa.String(length=TEXT_32),
            server_default=sa.text(f"'{EvidenceStatus.UNVERIFIED.value}'"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_classification_assignments_evidence_status",
        "classification_assignments",
        EVIDENCE_STATUS_CHECK,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_classification_assignments_evidence_status",
        "classification_assignments",
        type_="check",
    )
    op.drop_column("classification_assignments", "evidence_status")
    op.drop_column("classification_assignments", "provenance")
    op.drop_column("classification_assignments", "claim_id")
    op.drop_column("classification_assignments", "explanation")

    op.drop_constraint("ck_persons_birth_before_death", "persons", type_="check")
    op.drop_constraint("ck_persons_death_date", "persons", type_="check")
    op.drop_constraint("ck_persons_birth_date", "persons", type_="check")
    op.drop_column("persons", "external_identities")
    op.drop_column("persons", "death_precision")
    op.drop_column("persons", "death_year")
    op.drop_column("persons", "birth_precision")
    op.drop_column("persons", "birth_year")
    op.drop_column("persons", "aliases")
    op.create_index(
        PERSON_NAME_UNIQUE_CONSTRAINT,
        "persons",
        [sa.literal_column("lower(canonical_name)")],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
