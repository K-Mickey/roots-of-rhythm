"""PostgreSQL fixtures that wipe the controlled corpus tables."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from os import environ
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import delete, event
from sqlalchemy.engine import Engine, make_url

from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    ClaimEvidenceReferenceRecord,
    GenreRelationClaimRecord,
    ListeningGuideRecord,
    ListeningObservationRecord,
    RecordingOriginClaimEvidenceReferenceRecord,
    RecordingOriginClaimRecord,
    SourceFragmentRecord,
    SourceRecord,
    SourceVersionRecord,
)
from roots_of_rhythm.infrastructure.base import PgConfig
from roots_of_rhythm.infrastructure.database import create_database_engine
from roots_of_rhythm.infrastructure.pg_accessor import PgAccessor
from roots_of_rhythm.music_catalog.infrastructure.models import (
    ClassificationAssignmentRecord,
    ClassificationConceptRecord,
    GroupMembershipRecord,
    GroupRecord,
    LyricsVersionCreditRecord,
    LyricsVersionRecord,
    LyricsVersionRelationRecord,
    MusicalWorkRecord,
    RecordingCreditRecord,
    RecordingLyricsUsageRecord,
    RecordingRecord,
    RecordingWorkUsageRecord,
    WorkCreditRecord,
    WorkRelationRecord,
)
from roots_of_rhythm.people_catalog.infrastructure.models import PersonRecord

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from sqlalchemy.ext.asyncio import AsyncEngine


_CORPUS_TABLES = (
    ListeningObservationRecord,
    ListeningGuideRecord,
    RecordingOriginClaimEvidenceReferenceRecord,
    RecordingOriginClaimRecord,
    ClaimEvidenceReferenceRecord,
    GenreRelationClaimRecord,
    SourceFragmentRecord,
    SourceVersionRecord,
    SourceRecord,
    ClassificationAssignmentRecord,
    RecordingCreditRecord,
    RecordingLyricsUsageRecord,
    RecordingWorkUsageRecord,
    RecordingRecord,
    LyricsVersionRelationRecord,
    LyricsVersionCreditRecord,
    LyricsVersionRecord,
    WorkRelationRecord,
    WorkCreditRecord,
    GroupMembershipRecord,
    GroupRecord,
    MusicalWorkRecord,
    ClassificationConceptRecord,
    PersonRecord,
)

logger = logging.getLogger(__name__)


def _resolve_database_url() -> str:
    return environ["TEST_DATABASE_URL"]


async def _wipe_corpus(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        for table in _CORPUS_TABLES:
            await connection.execute(delete(table))


@contextmanager
def collect_select_statements() -> Iterator[list[str]]:
    statements: list[str] = []

    def _collect_statement(_conn: object, _cursor: object, statement: str, *_args: object, **_kwargs: object) -> None:
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(Engine, "before_cursor_execute", _collect_statement)
    try:
        yield statements
    finally:
        event.remove(Engine, "before_cursor_execute", _collect_statement)


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    database_engine = create_database_engine(_resolve_database_url())
    await _wipe_corpus(database_engine)
    yield database_engine
    await _wipe_corpus(database_engine)
    await database_engine.dispose()


@pytest.fixture
async def pg(engine: AsyncEngine) -> AsyncIterator[PgAccessor]:
    """Живой PgAccessor к тестовой БД (engine-параметр нужен для wipe-порядка)."""
    url = make_url(environ["TEST_DATABASE_URL"])
    config = PgConfig(
        database=url.database or "",
        host=url.host or "127.0.0.1",
        port=url.port or 5432,
        username=url.username,
        password=url.password,
    )
    accessor = PgAccessor(config)
    await accessor.connect()
    try:
        yield accessor
    finally:
        await close_leaked_pg_request_scope(accessor)
        await accessor.disconnect()


async def close_leaked_pg_request_scope(pg: PgAccessor) -> None:
    """Close a request scope leaked across tests under session-scoped asyncio loop.

    Production ``reset_request_scope()`` only clears the ContextVar and leaves the
    connection checked out (idle in transaction), which then blocks TRUNCATE/DROP.
    This test helper rolls back/closes the orphaned session so the pool can reuse it.
    """
    scope = pg._current_scope.get()
    if scope is None:
        return

    pg.reset_request_scope()
    scope._closed = True

    try:
        await scope._main_session.rollback()
    except Exception:
        logger.exception("failed to rollback leaked test pg session")

    try:
        await scope._main_session.close()
    except Exception:
        logger.exception("failed to close leaked test pg session")

    await scope.close_children()
