from typing import TYPE_CHECKING

import pytest
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.seed import genre_knowledge as genre_data
from tests.support.postgres import collect_select_statements

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


async def test_genre_sources_integration_returns_seeded_swing_bibliography(seeded_engine: AsyncEngine) -> None:
    database_url = seeded_engine.url.render_as_string(hide_password=False)
    with (
        TestClient(app=create_app(Settings(database_url=database_url))) as client,
        collect_select_statements() as selects,
    ):
        sources_response = client.get(f"/api/v1/genres/{genre_data.SWING_ID}/sources")

    assert sources_response.status_code == 200
    body = sources_response.json()
    assert body["genre_id"] == str(genre_data.SWING_ID)
    assert [item["id"] for item in body["sources"]] == [
        str(genre_data.SMITHSONIAN_SOURCE_ID),
        str(genre_data.LOC_SOURCE_ID),
    ]
    first, second = body["sources"]
    assert first["title"] == genre_data.SMITHSONIAN_TITLE
    assert first["author"] is None
    assert first["responsible_organization"] == genre_data.SMITHSONIAN_RESPONSIBLE_ORGANIZATION
    assert first["publication"] is None
    assert first["publication_date"] is None
    assert first["external_url"] == genre_data.SMITHSONIAN_EXTERNAL_URL
    assert second["title"] == genre_data.RHYTHM_AND_BLUES_NAME
    assert second["responsible_organization"] == genre_data.LOC_RESPONSIBLE_ORGANIZATION
    assert second["external_url"] == genre_data.LOC_EXTERNAL_URL

    with TestClient(
        app=create_app(Settings(database_url=seeded_engine.url.render_as_string(hide_password=False)))
    ) as client:
        relations_response = client.get(f"/api/v1/genres/{genre_data.SWING_ID}/relations")
    assert relations_response.status_code == 200
    relation_source_ids = {
        reference["source_id"]
        for relation in relations_response.json()["relations"]
        for reference in relation["evidence_references"]
    }
    bibliography_ids = {item["id"] for item in body["sources"]}
    assert relation_source_ids <= bibliography_ids

    assert len(selects) == 7
