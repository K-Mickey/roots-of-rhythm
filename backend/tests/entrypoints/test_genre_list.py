from litestar.di import Provide
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.discovery.application.dto import GenreListResponse, GenreSummary
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.entrypoints.dependencies import GENRE_LIST_READER_DEPENDENCY
from tests.discovery.fakes import StubGenreListReader


def _settings() -> Settings:
    return Settings(database_url="postgresql+psycopg://roots:roots@127.0.0.1:1/missing?connect_timeout=1")


def _reader_override(result: GenreListResponse | Exception) -> dict[str, Provide]:
    reader = StubGenreListReader(result)
    return {
        GENRE_LIST_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
    }


def test_genre_list_http_returns_200_shape() -> None:
    body = GenreListResponse(items=[GenreSummary(id="genre-1", name="Jazz")])
    with TestClient(app=create_app(_settings(), dependency_overrides=_reader_override(body))) as client:
        response = client.get("/api/v1/genres")

    assert response.status_code == 200
    assert response.json() == {"items": [{"id": "genre-1", "name": "Jazz"}]}


def test_genre_list_http_empty_is_success() -> None:
    with TestClient(
        app=create_app(_settings(), dependency_overrides=_reader_override(GenreListResponse(items=[]))),
    ) as client:
        response = client.get("/api/v1/genres")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_genre_list_http_unexpected_failure_is_internal_error() -> None:
    with TestClient(
        app=create_app(_settings(), dependency_overrides=_reader_override(RuntimeError("database details"))),
    ) as client:
        response = client.get("/api/v1/genres")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert body["message"] == "Не удалось загрузить материал."
    assert "database details" not in response.text
