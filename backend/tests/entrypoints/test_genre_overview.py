from uuid import uuid7

from litestar.di import Provide
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.discovery.application.dto import GenreOverviewResponse
from roots_of_rhythm.discovery.application.errors import (
    GenreOverviewAssemblyError,
    GenreOverviewNotFound,
)
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.entrypoints.dependencies import GENRE_OVERVIEW_READER_DEPENDENCY
from tests.discovery.fakes import StubGenreOverviewReader


def _settings() -> Settings:
    return Settings(database_url="postgresql+psycopg://roots:roots@127.0.0.1:1/missing?connect_timeout=1")


def _reader_override(result: GenreOverviewResponse | Exception) -> dict[str, Provide]:
    reader = StubGenreOverviewReader(result)
    return {
        GENRE_OVERVIEW_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
    }


def test_genre_overview_http_returns_200_shape() -> None:
    genre_id = uuid7()
    overview = GenreOverviewResponse(
        id=str(genre_id),
        name="Swing",
        definition="Published definition",
        primary_image=None,
        period=None,
        geography_or_origin=None,
        historical_context=None,
        formation=None,
        characteristic_features=[],
    )
    with TestClient(app=create_app(_settings(), dependency_overrides=_reader_override(overview))) as client:
        response = client.get(f"/api/v1/genres/{genre_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(genre_id),
        "name": "Swing",
        "definition": "Published definition",
        "primary_image": None,
        "period": None,
        "geography_or_origin": None,
        "historical_context": None,
        "formation": None,
        "characteristic_features": [],
    }


def test_genre_overview_http_malformed_id_is_not_found() -> None:
    with TestClient(
        app=create_app(_settings(), dependency_overrides=_reader_override(GenreOverviewNotFound("x"))),
    ) as client:
        response = client.get("/api/v1/genres/not-a-uuid")

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "GENRE_NOT_FOUND"
    assert body["message"] == "Материал не найден."
    assert body["details"] is None
    assert isinstance(body["request_id"], str)
    assert body["request_id"]


def test_genre_overview_http_reader_not_found_is_not_found() -> None:
    genre_id = uuid7()
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides=_reader_override(GenreOverviewNotFound(str(genre_id))),
        ),
    ) as client:
        response = client.get(f"/api/v1/genres/{genre_id}")

    assert response.status_code == 404
    assert response.json()["code"] == "GENRE_NOT_FOUND"


def test_genre_overview_http_assembly_failure_is_internal_error() -> None:
    genre_id = uuid7()
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides=_reader_override(GenreOverviewAssemblyError("broken")),
        ),
    ) as client:
        response = client.get(f"/api/v1/genres/{genre_id}")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert body["message"] == "Не удалось загрузить материал."
    assert body["details"] is None
    assert isinstance(body["request_id"], str)
    assert body["request_id"]


def test_genre_overview_http_unexpected_failure_is_internal_error() -> None:
    genre_id = uuid7()
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides=_reader_override(RuntimeError("database details")),
        ),
    ) as client:
        response = client.get(f"/api/v1/genres/{genre_id}")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert "database details" not in response.text
    assert isinstance(body["request_id"], str)
