from typing import TYPE_CHECKING

import pytest
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.seed import musical_works as work_data
from roots_of_rhythm.seed import recording_corpus as recording_data

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


async def test_recording_endpoints_return_seeded_corpus(seeded_engine: AsyncEngine) -> None:
    database_url = seeded_engine.url.render_as_string(hide_password=False)
    with TestClient(app=create_app(Settings(database_url=database_url))) as client:
        listing = client.get("/api/v1/recordings")
        ford = client.get(f"/api/v1/recordings/{recording_data.TENNESSEE_ERNIE_FORD_RECORDING_ID}")
        marian = client.get(f"/api/v1/recordings/{recording_data.MARIAN_RECORDING_ID}")

    assert listing.status_code == 200
    items = listing.json()["items"]
    assert [item["primary_credits"][0]["target"]["name"] for item in items] == [
        "Louis Armstrong",
        "Marian Anderson",
        "Merle Travis",
        "Stevie Wonder",
        "Tennessee Ernie Ford",
    ]
    assert {genre["name"] for item in items for genre in item["genres"]} == {
        "Country",
        "Rhythm and Blues",
    }

    assert ford.status_code == 200
    payload = ford.json()
    assert payload["id"] == str(recording_data.TENNESSEE_ERNIE_FORD_RECORDING_ID)
    assert payload["period"]["start"] == {"year": 1955, "precision": "exact_year"}
    assert payload["works"] == [
        {
            "work": {"id": str(work_data.SIXTEEN_TONS_ID), "name": "Sixteen Tons"},
            "usage_kind": "complete",
            "position": None,
        }
    ]
    assert [(item["language_tag"], item["creation_method"]) for item in payload["lyrics"]] == [
        ("en", "original"),
        ("ru", "machine_translation"),
    ]
    assert all(item["body"] is None for item in payload["lyrics"])
    assert payload["origin_badges"] == []
    assert payload["listening_guide"]["observations"][0]["feature"] == "Щелчки пальцами и пульс"

    assert marian.status_code == 200
    spiritual = marian.json()
    assert spiritual["period"]["start"] == {"year": 1924, "precision": "exact_year"}
    assert [(item["language_tag"], item["confirmed_for_recording"]) for item in spiritual["lyrics"]] == [
        ("en", False),
        ("ru", False),
    ]
    assert {item["body"] for item in spiritual["lyrics"]} == {
        recording_data.ENGLISH_BODY,
        recording_data.RUSSIAN_BODY,
    }
