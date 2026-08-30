"""Create recording lyrics usages.

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "recording_lyrics_usages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recording_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lyrics_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint("position > 0", name="ck_recording_lyrics_usages_position"),
        sa.ForeignKeyConstraint(["recording_id"], ["recordings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lyrics_version_id"], ["lyrics_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recording_lyrics_usages_recording_id", "recording_lyrics_usages", ["recording_id"])
    op.create_index("ix_recording_lyrics_usages_version_id", "recording_lyrics_usages", ["lyrics_version_id"])
    op.create_index(
        "uq_recording_lyrics_usages_recording_version",
        "recording_lyrics_usages",
        ["recording_id", "lyrics_version_id"],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
    op.create_index(
        "uq_recording_lyrics_usages_recording_position",
        "recording_lyrics_usages",
        ["recording_id", "position"],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
    op.execute(
        sa.text(
            """
            CREATE TRIGGER trg_recording_lyrics_usages_set_updated_at
            BEFORE UPDATE ON recording_lyrics_usages
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_recording_lyrics_usages_set_updated_at ON recording_lyrics_usages"))
    op.drop_table("recording_lyrics_usages")
