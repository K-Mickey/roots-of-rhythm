from uuid import uuid7

from litestar.di import Provide
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.discovery.application.dto import (
    ExternalIdentityView,
    GenreSummary,
    PerformerListResponse,
    PerformerOverviewResponse,
    PerformerSummary,
    PersonDateView,
)
from roots_of_rhythm.discovery.application.errors import PerformerOverviewNotFound
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.entrypoints.dependencies import (
    PERFORMER_LIST_READER_DEPENDENCY,
    PERFORMER_OVERVIEW_READER_DEPENDENCY,
)
from roots_of_rhythm.people_catalog.domain import TemporalPrecision
from tests.discovery.fakes import StubPerformerListReader, StubPerformerOverviewReader


def _settings() -> Settings:
    return Settings(database_url="postgresql+psycopg://roots:roots@127.0.0.1:1/missing?connect_timeout=1")


def test_performer_list_http_returns_200_shape() -> None:
    reader = StubPerformerListReader(
        PerformerListResponse(items=[PerformerSummary(id="performer-1", name="Louis Armstrong")]),
    )
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                PERFORMER_LIST_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get("/api/v1/performers")

    assert response.status_code == 200
    assert response.json() == {"items": [{"id": "performer-1", "name": "Louis Armstrong"}]}


def test_performer_overview_http_returns_all_public_fields() -> None:
    performer_id = uuid7()
    reader = StubPerformerOverviewReader(
        PerformerOverviewResponse(
            id=str(performer_id),
            name="Louis Armstrong",
            aliases=["Satchmo"],
            biography="Trumpeter and singer.",
            birth_date=PersonDateView(1901, TemporalPrecision.EXACT_YEAR),
            death_date=PersonDateView(1971, TemporalPrecision.EXACT_YEAR),
            external_identities=[
                ExternalIdentityView(
                    provider="MusicBrainz",
                    identifier="artist-1",
                    url="https://musicbrainz.org/artist/artist-1",
                ),
            ],
            primary_image=None,
            genres=[GenreSummary(id="genre-1", name="Jazz")],
        ),
    )
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                PERFORMER_OVERVIEW_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get(f"/api/v1/performers/{performer_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(performer_id),
        "name": "Louis Armstrong",
        "aliases": ["Satchmo"],
        "biography": "Trumpeter and singer.",
        "birth_date": {"year": 1901, "precision": "exact_year"},
        "death_date": {"year": 1971, "precision": "exact_year"},
        "external_identities": [
            {
                "provider": "MusicBrainz",
                "identifier": "artist-1",
                "url": "https://musicbrainz.org/artist/artist-1",
            },
        ],
        "primary_image": None,
        "genres": [{"id": "genre-1", "name": "Jazz"}],
    }


def test_performer_overview_http_malformed_id_is_not_found() -> None:
    reader = StubPerformerOverviewReader(PerformerOverviewNotFound("not-a-uuid"))
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                PERFORMER_OVERVIEW_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get("/api/v1/performers/not-a-uuid")

    assert response.status_code == 404
    assert response.json()["code"] == "PERFORMER_NOT_FOUND"


def test_performer_overview_http_unpublished_id_is_not_found() -> None:
    performer_id = uuid7()
    reader = StubPerformerOverviewReader(PerformerOverviewNotFound(str(performer_id)))
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                PERFORMER_OVERVIEW_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get(f"/api/v1/performers/{performer_id}")

    assert response.status_code == 404
    assert response.json()["code"] == "PERFORMER_NOT_FOUND"
