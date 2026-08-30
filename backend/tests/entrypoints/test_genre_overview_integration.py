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


async def test_genre_overview_integration_returns_seeded_swing_in_one_select(seeded_engine: AsyncEngine) -> None:
    database_url = seeded_engine.url.render_as_string(hide_password=False)
    with (
        TestClient(app=create_app(Settings(database_url=database_url))) as client,
        collect_select_statements() as selects,
    ):
        response = client.get(f"/api/v1/genres/{genre_data.SWING_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(genre_data.SWING_ID)
    assert body["name"] == "Swing"
    assert body["definition"] == genre_data.SWING_CONTENT.definition
    assert body["primary_image"] is None
    assert body["characteristic_features"] == []
    assert len(selects) == 1
