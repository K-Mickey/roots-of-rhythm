"""Create Music Catalog classification concepts.

Revision ID: 0001
Revises:
Create Date: 2026-08-17
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from roots_of_rhythm.music_catalog.infrastructure.models import (
    CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT,
    EDITORIAL_STATUS_CHECK,
    KIND_CHECK,
)
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_64, TEXT_1024

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "classification_concepts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(length=TEXT_32), nullable=False),
        sa.Column("editorial_status", sa.String(length=TEXT_32), nullable=False),
        sa.Column("canonical_name", sa.String(length=TEXT_64), nullable=False),
        sa.Column("aliases", postgresql.ARRAY(sa.String(length=TEXT_64)), nullable=False),
        sa.Column("definition", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("boundaries", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("period_label", sa.String(length=TEXT_64), nullable=True),
        sa.Column("period_start_year", sa.Integer(), nullable=True),
        sa.Column("period_start_precision", sa.String(length=TEXT_32), nullable=True),
        sa.Column("period_end_year", sa.Integer(), nullable=True),
        sa.Column("period_end_precision", sa.String(length=TEXT_32), nullable=True),
        sa.Column("geography_summary", sa.String(length=TEXT_64), nullable=True),
        sa.Column("historical_context", sa.String(length=TEXT_1024), nullable=True),
        sa.Column("formation", sa.String(length=TEXT_1024), nullable=True),
        sa.Column(
            "characteristic_features",
            postgresql.ARRAY(sa.String(length=TEXT_64)),
            nullable=False,
        ),
        sa.Column("primary_image_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(KIND_CHECK, name="ck_classification_concepts_kind"),
        sa.CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_classification_concepts_editorial_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT,
        "classification_concepts",
        ["kind", sa.literal_column("lower(canonical_name)")],
        unique=True,
    )
    op.create_index(
        "ix_classification_concepts_kind_editorial_status",
        "classification_concepts",
        ["kind", "editorial_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_classification_concepts_kind_editorial_status", table_name="classification_concepts")
    op.drop_index(CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT, table_name="classification_concepts")
    op.drop_table("classification_concepts")
