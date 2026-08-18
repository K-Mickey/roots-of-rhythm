"""Expand Source with bibliographic metadata fields.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-18
"""

import sqlalchemy as sa
from alembic import op

from roots_of_rhythm.historical_knowledge.domain.value_objects import SHORT_TEXT_MAX_LENGTH, URL_MAX_LENGTH

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.alter_column(
        "sources",
        "institution_name",
        new_column_name="responsible_organization",
        existing_type=sa.String(length=SHORT_TEXT_MAX_LENGTH),
        existing_nullable=True,
    )
    op.add_column("sources", sa.Column("author", sa.String(length=SHORT_TEXT_MAX_LENGTH), nullable=True))
    op.add_column("sources", sa.Column("publication", sa.String(length=SHORT_TEXT_MAX_LENGTH), nullable=True))
    op.add_column("sources", sa.Column("publication_date", sa.String(length=SHORT_TEXT_MAX_LENGTH), nullable=True))
    op.add_column("sources", sa.Column("external_url", sa.String(length=URL_MAX_LENGTH), nullable=True))


def downgrade() -> None:
    op.drop_column("sources", "external_url")
    op.drop_column("sources", "publication_date")
    op.drop_column("sources", "publication")
    op.drop_column("sources", "author")
    op.alter_column(
        "sources",
        "responsible_organization",
        new_column_name="institution_name",
        existing_type=sa.String(length=SHORT_TEXT_MAX_LENGTH),
        existing_nullable=True,
    )
