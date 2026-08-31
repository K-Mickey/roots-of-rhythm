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


async def test_genre_relations_integration_returns_seeded_swing_cards(seeded_engine: AsyncEngine) -> None:
    database_url = seeded_engine.url.render_as_string(hide_password=False)
    with (
        TestClient(app=create_app(Settings(database_url=database_url))) as client,
        collect_select_statements() as selects,
    ):
        response = client.get(f"/api/v1/genres/{genre_data.SWING_ID}/relations")

    assert response.status_code == 200
    body = response.json()
    assert body["genre_id"] == str(genre_data.SWING_ID)
    assert len(body["relations"]) == 2
    first, second = body["relations"]
    assert first["id"] == str(genre_data.SWING_FROM_JAZZ_CLAIM_ID)
    assert first["related_genre"]["id"] == str(genre_data.JAZZ_ID)
    assert first["related_genre"]["name"] == "Jazz"
    assert first["relation_type"] == "developed_from"
    assert first["perspective"] == "subject"
    assert first["explanation"] == genre_data.SWING_FROM_JAZZ_EXPLANATION
    assert first["evidence_status"] == "supported"
    assert len(first["evidence_references"]) >= 1
    assert second["id"] == str(genre_data.SWING_TO_JUMP_CLAIM_ID)
    assert second["related_genre"]["id"] == str(genre_data.JUMP_BLUES_ID)
    assert second["related_genre"]["name"] == "Jump Blues"
    assert second["relation_type"] == "contributed_to_emergence_of"
    assert second["perspective"] == "subject"
    assert len(selects) == 5
