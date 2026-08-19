"""Create persons and classification assignments.

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from roots_of_rhythm.music_catalog.infrastructure.models import (
    CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT,
    EDITORIAL_STATUS_CHECK,
    TARGET_KIND_CHECK,
)
from roots_of_rhythm.people_catalog.domain.value_objects import LONG_TEXT_MAX_LENGTH, SHORT_TEXT_MAX_LENGTH
from roots_of_rhythm.people_catalog.infrastructure.models import (
    EDITORIAL_STATUS_CHECK as PERSON_EDITORIAL_STATUS_CHECK,
)
from roots_of_rhythm.people_catalog.infrastructure.models import PERSON_NAME_UNIQUE_CONSTRAINT

revision: str = "0005"
down_revision: str | None = "0004"
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
        "persons",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("editorial_status", sa.String(length=32), nullable=False),
        sa.Column("canonical_name", sa.String(length=SHORT_TEXT_MAX_LENGTH), nullable=False),
        sa.Column("biography", sa.String(length=LONG_TEXT_MAX_LENGTH), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(PERSON_EDITORIAL_STATUS_CHECK, name="ck_persons_editorial_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        PERSON_NAME_UNIQUE_CONSTRAINT,
        "persons",
        [sa.literal_column("lower(canonical_name)")],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
    op.create_index("ix_persons_editorial_status", "persons", ["editorial_status"], unique=False)
    _create_updated_at_trigger("persons")

    op.create_table(
        "classification_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_kind", sa.String(length=32), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("editorial_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(TARGET_KIND_CHECK, name="ck_classification_assignments_target_kind"),
        sa.CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_classification_assignments_editorial_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT,
        "classification_assignments",
        ["target_kind", "target_id", "concept_id"],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
    op.create_index(
        "ix_classification_assignments_target",
        "classification_assignments",
        ["target_kind", "target_id"],
        unique=False,
    )
    _create_updated_at_trigger("classification_assignments")


def downgrade() -> None:
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_classification_assignments_set_updated_at ON classification_assignments")
    )
    op.drop_index("ix_classification_assignments_target", table_name="classification_assignments")
    op.drop_index(CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT, table_name="classification_assignments")
    op.drop_table("classification_assignments")
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_persons_set_updated_at ON persons"))
    op.drop_index("ix_persons_editorial_status", table_name="persons")
    op.drop_index(PERSON_NAME_UNIQUE_CONSTRAINT, table_name="persons")
    op.drop_table("persons")
