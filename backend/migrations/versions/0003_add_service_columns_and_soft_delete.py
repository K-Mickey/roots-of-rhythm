"""Add service columns and soft-delete support.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-18
"""

import sqlalchemy as sa
from alembic import op

from roots_of_rhythm.historical_knowledge.infrastructure.models import CLAIM_ENDPOINTS_UNIQUE_INDEX
from roots_of_rhythm.music_catalog.infrastructure.models import CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

TABLES = (
    "classification_concepts",
    "sources",
    "source_versions",
    "source_fragments",
    "genre_relation_claims",
    "claim_evidence_references",
)

_SET_UPDATED_AT_FUNCTION = """
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


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
    for table_name in TABLES:
        op.add_column(
            table_name,
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.add_column(
            table_name,
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.add_column(
            table_name,
            sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        )

    op.execute(sa.text(_SET_UPDATED_AT_FUNCTION))
    for table_name in TABLES:
        _create_updated_at_trigger(table_name)

    op.drop_index(CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT, table_name="classification_concepts")
    op.create_index(
        CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT,
        "classification_concepts",
        ["kind", sa.literal_column("lower(canonical_name)")],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )

    op.drop_constraint("uq_genre_relation_claims_endpoints_type", "genre_relation_claims", type_="unique")
    op.create_index(
        CLAIM_ENDPOINTS_UNIQUE_INDEX,
        "genre_relation_claims",
        ["subject_genre_id", "target_genre_id", "relation_type"],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )


def downgrade() -> None:
    op.drop_index(CLAIM_ENDPOINTS_UNIQUE_INDEX, table_name="genre_relation_claims")
    op.create_unique_constraint(
        "uq_genre_relation_claims_endpoints_type",
        "genre_relation_claims",
        ["subject_genre_id", "target_genre_id", "relation_type"],
    )

    op.drop_index(CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT, table_name="classification_concepts")
    op.create_index(
        CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT,
        "classification_concepts",
        ["kind", sa.literal_column("lower(canonical_name)")],
        unique=True,
    )

    for table_name in TABLES:
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS trg_{table_name}_set_updated_at ON {table_name}"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS set_updated_at()"))

    for table_name in TABLES:
        op.drop_column(table_name, "deleted")
        op.drop_column(table_name, "updated_at")
        op.drop_column(table_name, "created_at")
