from uuid import uuid7

from litestar.di import Provide
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.discovery.application.dto import GenreSourcesResponse, SourceView
from roots_of_rhythm.discovery.application.errors import (
    GenreSourcesAssemblyError,
    GenreSourcesNotFound,
)
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.entrypoints.dependencies import GENRE_SOURCES_READER_DEPENDENCY
from tests.discovery.fakes import StubGenreSourcesReader


def _settings() -> Settings:
    return Settings(database_url="postgresql+psycopg://roots:roots@127.0.0.1:1/missing?connect_timeout=1")


def _reader_override(result: GenreSourcesResponse | Exception) -> dict[str, Provide]:
    reader = StubGenreSourcesReader(result)
    return {
        GENRE_SOURCES_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
    }


def test_genre_sources_http_returns_200_shape() -> None:
    genre_id = uuid7()
    source_id = uuid7()
    body = GenreSourcesResponse(
        genre_id=str(genre_id),
        sources=[
            SourceView(
                id=str(source_id),
                title="Jazz",
                author=None,
                responsible_organization="Smithsonian Music",
                publication=None,
                publication_date=None,
                external_url="https://music.si.edu/story/jazz",
            )
        ],
    )
    with TestClient(app=create_app(_settings(), dependency_overrides=_reader_override(body))) as client:
        response = client.get(f"/api/v1/genres/{genre_id}/sources")

    assert response.status_code == 200
    assert response.json() == {
        "genre_id": str(genre_id),
        "sources": [
            {
                "id": str(source_id),
                "title": "Jazz",
                "author": None,
                "responsible_organization": "Smithsonian Music",
                "publication": None,
                "publication_date": None,
                "external_url": "https://music.si.edu/story/jazz",
            }
        ],
    }


def test_genre_sources_http_malformed_id_is_not_found() -> None:
    with TestClient(
        app=create_app(_settings(), dependency_overrides=_reader_override(GenreSourcesNotFound("x"))),
    ) as client:
        response = client.get("/api/v1/genres/not-a-uuid/sources")

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "GENRE_NOT_FOUND"
    assert body["message"] == "Материал не найден."
    assert body["details"] is None
    assert isinstance(body["request_id"], str)
    assert body["request_id"]


def test_genre_sources_http_reader_not_found_is_not_found() -> None:
    genre_id = uuid7()
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides=_reader_override(GenreSourcesNotFound(str(genre_id))),
        ),
    ) as client:
        response = client.get(f"/api/v1/genres/{genre_id}/sources")

    assert response.status_code == 404
    assert response.json()["code"] == "GENRE_NOT_FOUND"


def test_genre_sources_http_assembly_failure_is_internal_error() -> None:
    genre_id = uuid7()
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides=_reader_override(GenreSourcesAssemblyError("broken")),
        ),
    ) as client:
        response = client.get(f"/api/v1/genres/{genre_id}/sources")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert body["message"] == "Не удалось загрузить материал."
    assert body["details"] is None
    assert isinstance(body["request_id"], str)
    assert body["request_id"]


def test_genre_sources_http_unexpected_failure_is_internal_error() -> None:
    genre_id = uuid7()
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides=_reader_override(RuntimeError("database details")),
        ),
    ) as client:
        response = client.get(f"/api/v1/genres/{genre_id}/sources")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert "database details" not in response.text
    assert isinstance(body["request_id"], str)
