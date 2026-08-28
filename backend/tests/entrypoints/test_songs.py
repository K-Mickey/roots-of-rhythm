from uuid import uuid7

from litestar.di import Provide
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.discovery.application.dto import (
    GenreSummary,
    SongListResponse,
    SongOverviewResponse,
    SongPeriodView,
    SongSummary,
    SongWorkCreditView,
    PerformerSummary,
)
from roots_of_rhythm.discovery.application.errors import SongOverviewNotFound
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.entrypoints.dependencies import (
    SONG_LIST_READER_DEPENDENCY,
    SONG_OVERVIEW_READER_DEPENDENCY,
)
from roots_of_rhythm.music_catalog.domain import WorkCreditRole
from tests.discovery.fakes import StubSongListReader, StubSongOverviewReader


def _settings() -> Settings:
    return Settings(database_url="postgresql+psycopg://roots:roots@127.0.0.1:1/missing?connect_timeout=1")


def test_song_list_http_returns_200_shape() -> None:
    reader = StubSongListReader(
        SongListResponse(items=[SongSummary(id="song-1", name="Sixteen Tons")]),
    )
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                SONG_LIST_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get("/api/v1/songs")

    assert response.status_code == 200
    assert response.json() == {"items": [{"id": "song-1", "name": "Sixteen Tons"}]}


def test_song_list_http_internal_error_does_not_use_song_not_found() -> None:
    reader = StubSongListReader(RuntimeError("database unavailable"))
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                SONG_LIST_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get("/api/v1/songs")

    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"


def test_song_overview_http_returns_all_public_fields() -> None:
    song_id = uuid7()
    reader = StubSongOverviewReader(
        SongOverviewResponse(
            id=str(song_id),
            name="Sixteen Tons",
            aliases=["16 Tons"],
            description="A coal-mining song.",
            period=SongPeriodView(start=None, end=None),
            external_identities=[],
            credits=[
                SongWorkCreditView(
                    person=PerformerSummary(id="person-1", name="Merle Travis"),
                    role=WorkCreditRole.COMPOSER,
                    credited_as=None,
                ),
            ],
            classifications=[GenreSummary(id="genre-1", name="Country")],
            related_works=[],
            lyrics_versions=[],
        ),
    )
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                SONG_OVERVIEW_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get(f"/api/v1/songs/{song_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(song_id),
        "name": "Sixteen Tons",
        "aliases": ["16 Tons"],
        "description": "A coal-mining song.",
        "period": {"start": None, "end": None},
        "external_identities": [],
        "credits": [
            {
                "person": {"id": "person-1", "name": "Merle Travis"},
                "role": "composer",
                "credited_as": None,
            },
        ],
        "classifications": [{"id": "genre-1", "name": "Country"}],
        "related_works": [],
        "lyrics_versions": [],
    }


def test_song_overview_http_malformed_id_is_not_found() -> None:
    reader = StubSongOverviewReader(SongOverviewNotFound("not-a-uuid"))
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                SONG_OVERVIEW_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get("/api/v1/songs/not-a-uuid")

    assert response.status_code == 404
    assert response.json()["code"] == "SONG_NOT_FOUND"


def test_song_overview_http_unpublished_id_is_not_found() -> None:
    song_id = uuid7()
    reader = StubSongOverviewReader(SongOverviewNotFound(str(song_id)))
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                SONG_OVERVIEW_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get(f"/api/v1/songs/{song_id}")

    assert response.status_code == 404
    assert response.json()["code"] == "SONG_NOT_FOUND"
