"""Schema-level ADR-0005 contract check.

Every ORM table must carry ``created_at``/``updated_at``/``deleted`` columns
(non-null, DB-owned defaults) and a ``BEFORE UPDATE`` trigger that bumps
``updated_at``. This guards against new tables bypassing the service-columns
and soft-delete contract defined by ADR-0005.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text

from roots_of_rhythm.historical_knowledge.infrastructure.models import HistoricalKnowledgeBase
from roots_of_rhythm.music_catalog.infrastructure.models import MusicCatalogBase
from roots_of_rhythm.people_catalog.infrastructure.models import PeopleCatalogBase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration

SERVICE_COLUMNS = ("created_at", "updated_at", "deleted")


def _all_tables() -> set[str]:
    tables: set[str] = set()
    for base in (MusicCatalogBase, HistoricalKnowledgeBase, PeopleCatalogBase):
        tables.update(base.metadata.tables)
    return tables


async def _non_null_service_columns(engine: AsyncEngine, table_name: str) -> list[str]:
    async with engine.connect() as connection:
        rows = await connection.execute(
            text(
                "SELECT column_name, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = :table "
                "AND column_name IN ('created_at', 'updated_at', 'deleted')"
            ),
            {"table": table_name},
        )
        by_name: dict[str, str] = {row[0]: row[1] for row in rows}
    missing = [column for column in SERVICE_COLUMNS if column not in by_name]
    nullable = [column for column, is_nullable in by_name.items() if is_nullable == "YES"]
    return missing + nullable


async def _has_updated_at_trigger(engine: AsyncEngine, table_name: str) -> bool:
    async with engine.connect() as connection:
        result = await connection.execute(
            text(
                "SELECT count(*) FROM pg_trigger tr "
                "JOIN pg_class c ON c.oid = tr.tgrelid "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'public' AND c.relname = :table "
                "AND NOT tr.tgisinternal AND tr.tgname = :trigger"
            ),
            {"table": table_name, "trigger": f"trg_{table_name}_set_updated_at"},
        )
        count: int = result.scalar_one()
        return count == 1


async def test_all_tables_follow_service_columns_and_update_trigger_contract(engine: AsyncEngine) -> None:
    failures: list[str] = []
    for table_name in sorted(_all_tables()):
        columns_issues = await _non_null_service_columns(engine, table_name)
        if columns_issues:
            failures.append(f"{table_name}: service columns missing or nullable: {', '.join(columns_issues)}")
        if not await _has_updated_at_trigger(engine, table_name):
            failures.append(f"{table_name}: missing trg_{table_name}_set_updated_at trigger")

    assert not failures, "ADR-0005 schema contract violations:\n" + "\n".join(failures)
