from typing import TYPE_CHECKING

import pytest
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.seed import corpus as data

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


async def test_genre_list_integration_returns_seeded_names_in_order(seeded_engine: AsyncEngine) -> None:
    database_url = seeded_engine.url.render_as_string(hide_password=False)
    with TestClient(app=create_app(Settings(database_url=database_url))) as client:
        response = client.get("/api/v1/genres")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"id": str(data.JAZZ_ID), "name": "Jazz"},
            {"id": str(data.JUMP_BLUES_ID), "name": "Jump Blues"},
            {"id": str(data.SWING_ID), "name": "Swing"},
        ]
    }
