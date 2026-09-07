"""Ensure set_updated_at trigger on recording origin claims.

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-07
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

_TABLES = (
    "recording_origin_claims",
    "recording_origin_claim_evidence_references",
)


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
    for table_name in _TABLES:
        _create_updated_at_trigger(table_name)


def downgrade() -> None:
    for table_name in _TABLES:
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS trg_{table_name}_set_updated_at ON {table_name}"))
