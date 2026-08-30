from typing import TYPE_CHECKING

import pytest
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.seed import genre_knowledge as genre_data
from roots_of_rhythm.seed import musical_works as work_data
from roots_of_rhythm.seed import recording_corpus as recording_data

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
            {"id": str(work_data.NOBODY_KNOWS_TROUBLE_ID), "name": "Nobody Knows the Trouble I've Seen"},
            {"id": str(work_data.ONE_O_CLOCK_JUMP_ID), "name": "One O'Clock Jump"},
            {"id": str(work_data.ORNITHOLOGY_ID), "name": "Ornithology"},
            {"id": str(work_data.SHAKE_RATTLE_AND_ROLL_ID), "name": "Shake, Rattle and Roll"},
            {"id": str(work_data.SING_SING_SING_ID), "name": "Sing, Sing, Sing (With a Swing)"},
            {"id": str(work_data.SIXTEEN_TONS_ID), "name": "Sixteen Tons"},
            {"id": str(work_data.WEST_END_BLUES_ID), "name": "West End Blues"},
        ],
    }


async def test_spiritual_overview_exposes_fallback_lyrics(seeded_engine: AsyncEngine) -> None:
    database_url = seeded_engine.url.render_as_string(hide_password=False)
    with TestClient(app=create_app(Settings(database_url=database_url))) as client:
        response = client.get(f"/api/v1/songs/{work_data.NOBODY_KNOWS_TROUBLE_ID}")

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["recordings"]] == [
        str(recording_data.MARIAN_RECORDING_ID),
        str(recording_data.LOUIS_RECORDING_ID),
    ]
    assert {item["body"] for item in payload["lyrics_versions"]} == {
        recording_data.ENGLISH_BODY,
        recording_data.RUSSIAN_BODY,
    }


async def test_song_overview_integration_returns_seeded_credits(seeded_engine: AsyncEngine) -> None:
    database_url = seeded_engine.url.render_as_string(hide_password=False)
    with TestClient(app=create_app(Settings(database_url=database_url))) as client:
        response = client.get(f"/api/v1/songs/{work_data.SIXTEEN_TONS_ID}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(work_data.SIXTEEN_TONS_ID)
    assert payload["name"] == "Sixteen Tons"
    assert payload["classifications"] == []
    assert payload["related_works"] == []
    assert {item["id"] for item in payload["lyrics_versions"]} == {
        str(recording_data.SIXTEEN_TONS_EN_LYRICS_ID),
        str(recording_data.SIXTEEN_TONS_RU_READING_ID),
    }
    assert all(item["credits"] == [] for item in payload["lyrics_versions"])
    assert payload["recording_genres"] == [
        {"genre": {"id": str(genre_data.COUNTRY_ID), "name": "Country"}, "recording_count": 2},
        {
            "genre": {"id": str(genre_data.RHYTHM_AND_BLUES_ID), "name": "Rhythm and Blues"},
            "recording_count": 1,
        },
    ]
    assert [item["id"] for item in payload["recordings"]] == [
        str(recording_data.MERLE_TRAVIS_RECORDING_ID),
        str(recording_data.TENNESSEE_ERNIE_FORD_RECORDING_ID),
        str(recording_data.STEVIE_WONDER_RECORDING_ID),
    ]
    assert payload["recordings"][0]["origin_badges"] == ["first_recording_of"]
    assert [(credit["person"]["name"], credit["role"]) for credit in payload["credits"]] == [
        ("Merle Travis", "composer"),
        ("Merle Travis", "lyricist"),
    ]
