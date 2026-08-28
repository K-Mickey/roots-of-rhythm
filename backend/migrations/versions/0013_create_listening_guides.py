"""Create listening guides.

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    service_columns = (
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_table(
        "listening_guides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recording_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("editorial_status", sa.String(32), nullable=False),
        *service_columns,
        sa.CheckConstraint(
            "editorial_status IN ('draft', 'in_review', 'published', 'archived')",
            name="ck_listening_guides_editorial_status",
        ),
    )
    op.create_index(
        "uq_listening_guides_active_recording",
        "listening_guides",
        ["recording_id"],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
    op.create_table(
        "listening_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "guide_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("listening_guides.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("feature", sa.String(64), nullable=False),
        sa.Column("explanation", sa.String(1024), nullable=False),
        sa.Column("context", sa.String(1024)),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("authored_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("start_seconds", sa.Integer()),
        sa.Column("end_seconds", sa.Integer()),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint("position > 0", name="ck_listening_observations_position"),
        sa.CheckConstraint(
            "(start_seconds IS NULL AND end_seconds IS NULL) OR (start_seconds >= 0 AND end_seconds > start_seconds)",
            name="ck_listening_observations_range",
        ),
    )
    op.create_index("ix_listening_observations_guide_id", "listening_observations", ["guide_id"])
    op.create_index(
        "uq_listening_observations_active_position",
        "listening_observations",
        ["guide_id", "position"],
        unique=True,
        postgresql_where=sa.text("deleted = false"),
    )
    for table in ("listening_guides", "listening_observations"):
        op.execute(
            sa.text(
                f"CREATE TRIGGER trg_{table}_set_updated_at BEFORE UPDATE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
            )
        )


def downgrade() -> None:
    op.drop_table("listening_observations")
    op.drop_table("listening_guides")
