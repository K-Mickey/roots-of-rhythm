"""PostgreSQL fixtures that wipe the controlled corpus tables."""

from __future__ import annotations

from os import environ
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import delete

from roots_of_rhythm.config import settings
from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    ClaimEvidenceReferenceRecord,
    GenreRelationClaimRecord,
    SourceFragmentRecord,
    SourceRecord,
    SourceVersionRecord,
)
from roots_of_rhythm.infrastructure.database import create_database_engine
from roots_of_rhythm.music_catalog.infrastructure.models import ClassificationConceptRecord

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncEngine

_CORPUS_TABLES = (
    ClaimEvidenceReferenceRecord,
    GenreRelationClaimRecord,
    SourceFragmentRecord,
    SourceVersionRecord,
    SourceRecord,
    ClassificationConceptRecord,
)


async def _wipe_corpus(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        for table in _CORPUS_TABLES:
            await connection.execute(delete(table))


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    database_url = environ.get("TEST_DATABASE_URL", settings.database_url)
    database_engine = create_database_engine(database_url)
    await _wipe_corpus(database_engine)
    yield database_engine
    await _wipe_corpus(database_engine)
    await database_engine.dispose()
