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


async def test_genre_sources_integration_returns_seeded_swing_bibliography(engine: AsyncEngine) -> None:
    await CorpusSeedRunner(create_session_factory(engine)).run()

    statements: list[str] = []

    def _count_statement(_conn: object, _cursor: object, statement: str, *_args: object, **_kwargs: object) -> None:
        statements.append(statement)

    event.listen(Engine, "before_cursor_execute", _count_statement)
    try:
        database_url = engine.url.render_as_string(hide_password=False)
        with TestClient(app=create_app(Settings(database_url=database_url))) as client:
            sources_response = client.get(f"/api/v1/genres/{data.SWING_ID}/sources")
    finally:
        event.remove(Engine, "before_cursor_execute", _count_statement)

    assert sources_response.status_code == 200
    body = sources_response.json()
    assert body["genre_id"] == str(data.SWING_ID)
    assert [item["id"] for item in body["sources"]] == [
        str(data.SMITHSONIAN_SOURCE_ID),
        str(data.LOC_SOURCE_ID),
    ]
    first, second = body["sources"]
    assert first["title"] == data.SMITHSONIAN_TITLE
    assert first["author"] is None
    assert first["responsible_organization"] == data.SMITHSONIAN_RESPONSIBLE_ORGANIZATION
    assert first["publication"] is None
    assert first["publication_date"] is None
    assert first["external_url"] == data.SMITHSONIAN_EXTERNAL_URL
    assert second["title"] == data.LOC_TITLE
    assert second["responsible_organization"] == data.LOC_RESPONSIBLE_ORGANIZATION
    assert second["external_url"] == data.LOC_EXTERNAL_URL

    with TestClient(app=create_app(Settings(database_url=engine.url.render_as_string(hide_password=False)))) as client:
        relations_response = client.get(f"/api/v1/genres/{data.SWING_ID}/relations")
    assert relations_response.status_code == 200
    relation_source_ids = {
        reference["source_id"]
        for relation in relations_response.json()["relations"]
        for reference in relation["evidence_references"]
    }
    bibliography_ids = {item["id"] for item in body["sources"]}
    assert relation_source_ids <= bibliography_ids

    selects = [statement for statement in statements if statement.lstrip().upper().startswith("SELECT")]
    assert len(selects) == 7
