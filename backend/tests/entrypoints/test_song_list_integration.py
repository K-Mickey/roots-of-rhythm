from typing import TYPE_CHECKING

import pytest
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.seed import corpus as data

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


async def test_song_list_integration_returns_seeded_titles_in_order(seeded_engine: AsyncEngine) -> None:
    database_url = seeded_engine.url.render_as_string(hide_password=False)
    with TestClient(app=create_app(Settings(database_url=database_url))) as client:
        response = client.get("/api/v1/songs")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"id": str(data.ONE_O_CLOCK_JUMP_ID), "name": "One O'Clock Jump"},
            {"id": str(data.ORNITHOLOGY_ID), "name": "Ornithology"},
            {"id": str(data.SHAKE_RATTLE_AND_ROLL_ID), "name": "Shake, Rattle and Roll"},
            {"id": str(data.SING_SING_SING_ID), "name": "Sing, Sing, Sing (With a Swing)"},
            {"id": str(data.SIXTEEN_TONS_ID), "name": "Sixteen Tons"},
            {"id": str(data.WEST_END_BLUES_ID), "name": "West End Blues"},
        ],
    }


async def test_song_overview_integration_returns_seeded_credits(seeded_engine: AsyncEngine) -> None:
    database_url = seeded_engine.url.render_as_string(hide_password=False)
    with TestClient(app=create_app(Settings(database_url=database_url))) as client:
        response = client.get(f"/api/v1/songs/{data.SIXTEEN_TONS_ID}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(data.SIXTEEN_TONS_ID)
    assert payload["name"] == "Sixteen Tons"
    assert payload["classifications"] == []
    assert payload["related_works"] == []
    assert payload["lyrics_versions"] == []
    assert [(credit["person"]["name"], credit["role"]) for credit in payload["credits"]] == [
        ("Merle Travis", "composer"),
        ("Merle Travis", "lyricist"),
    ]
