from os import environ
from typing import TYPE_CHECKING

import pytest
from litestar.testing import TestClient
from sqlalchemy import delete, event
from sqlalchemy.engine import Engine

from roots_of_rhythm.config import Settings, settings
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    ClaimEvidenceReferenceRecord,
    GenreRelationClaimRecord,
    SourceFragmentRecord,
    SourceRecord,
    SourceVersionRecord,
)
from roots_of_rhythm.infrastructure.database import create_database_engine, create_session_factory
from roots_of_rhythm.music_catalog.infrastructure.models import ClassificationConceptRecord
from roots_of_rhythm.seed import CorpusSeedRunner
from roots_of_rhythm.seed import corpus as data

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    database_url = environ.get("TEST_DATABASE_URL", settings.database_url)
    database_engine = create_database_engine(database_url)
    async with database_engine.begin() as connection:
        await connection.execute(delete(ClaimEvidenceReferenceRecord))
        await connection.execute(delete(GenreRelationClaimRecord))
        await connection.execute(delete(SourceFragmentRecord))
        await connection.execute(delete(SourceVersionRecord))
        await connection.execute(delete(SourceRecord))
        await connection.execute(delete(ClassificationConceptRecord))
    yield database_engine
    async with database_engine.begin() as connection:
        await connection.execute(delete(ClaimEvidenceReferenceRecord))
        await connection.execute(delete(GenreRelationClaimRecord))
        await connection.execute(delete(SourceFragmentRecord))
        await connection.execute(delete(SourceVersionRecord))
        await connection.execute(delete(SourceRecord))
        await connection.execute(delete(ClassificationConceptRecord))
    await database_engine.dispose()


async def test_genre_overview_integration_returns_seeded_swing_in_one_select(engine: AsyncEngine) -> None:
    await CorpusSeedRunner(create_session_factory(engine)).run()

    statements: list[str] = []

    def _count_statement(_conn: object, _cursor: object, statement: str, *_args: object, **_kwargs: object) -> None:
        statements.append(statement)

    event.listen(Engine, "before_cursor_execute", _count_statement)
    try:
        database_url = engine.url.render_as_string(hide_password=False)
        with TestClient(app=create_app(Settings(database_url=database_url))) as client:
            response = client.get(f"/api/v1/genres/{data.SWING_ID}")
    finally:
        event.remove(Engine, "before_cursor_execute", _count_statement)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(data.SWING_ID)
    assert body["name"] == "Swing"
    assert body["definition"] == data.SWING_CONTENT.definition
    assert body["primary_image"] is None
    assert body["characteristic_features"] == []
    selects = [statement for statement in statements if statement.lstrip().upper().startswith("SELECT")]
    assert len(selects) == 1
