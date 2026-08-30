from uuid import uuid7

from litestar.di import Provide
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.discovery.application.dto.common import (
    GenreSummary,
    RelationPerspective,
)
from roots_of_rhythm.discovery.application.dto.genres import (
    GenreRelationsResponse,
    GenreRelationView,
)
from roots_of_rhythm.discovery.application.errors.genres import (
    GenreRelationsAssemblyError,
    GenreRelationsNotFound,
)
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.entrypoints.dependencies import GENRE_RELATIONS_READER_DEPENDENCY
from roots_of_rhythm.historical_knowledge.domain import EvidenceStatus, RelationType
from tests.discovery.fakes import StubGenreRelationsReader


def _settings() -> Settings:
    return Settings(database_url="postgresql+psycopg://roots:roots@127.0.0.1:1/missing?connect_timeout=1")


def _reader_override(result: GenreRelationsResponse | Exception) -> dict[str, Provide]:
    reader = StubGenreRelationsReader(result)
    return {
        GENRE_RELATIONS_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
    }


def test_genre_relations_http_returns_200_shape() -> None:
    genre_id = uuid7()
    related_id = uuid7()
    claim_id = uuid7()
    body = GenreRelationsResponse(
        genre_id=str(genre_id),
        relations=[
            GenreRelationView(
                id=str(claim_id),
                related_genre=GenreSummary(id=str(related_id), name="Jazz"),
                relation_type=RelationType.DEVELOPED_FROM,
                perspective=RelationPerspective.SUBJECT,
                explanation="Swing developed from Jazz.",
                temporal_context=None,
                geographic_context=None,
                evidence_status=EvidenceStatus.SUPPORTED,
                evidence_references=[],
            )
        ],
    )
    with TestClient(app=create_app(_settings(), dependency_overrides=_reader_override(body))) as client:
        response = client.get(f"/api/v1/genres/{genre_id}/relations")

    assert response.status_code == 200
    assert response.json() == {
        "genre_id": str(genre_id),
        "relations": [
            {
                "id": str(claim_id),
                "related_genre": {"id": str(related_id), "name": "Jazz"},
                "relation_type": "developed_from",
                "perspective": "subject",
                "explanation": "Swing developed from Jazz.",
                "temporal_context": None,
                "geographic_context": None,
                "evidence_status": "supported",
                "evidence_references": [],
            }
        ],
    }


def test_genre_relations_http_malformed_id_is_not_found() -> None:
    with TestClient(
        app=create_app(_settings(), dependency_overrides=_reader_override(GenreRelationsNotFound("x"))),
    ) as client:
        response = client.get("/api/v1/genres/not-a-uuid/relations")

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "GENRE_NOT_FOUND"
    assert body["message"] == "Материал не найден."
    assert body["details"] is None
    assert isinstance(body["request_id"], str)
    assert body["request_id"]


def test_genre_relations_http_reader_not_found_is_not_found() -> None:
    genre_id = uuid7()
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides=_reader_override(GenreRelationsNotFound(str(genre_id))),
        ),
    ) as client:
        response = client.get(f"/api/v1/genres/{genre_id}/relations")

    assert response.status_code == 404
    assert response.json()["code"] == "GENRE_NOT_FOUND"


def test_genre_relations_http_assembly_failure_is_internal_error() -> None:
    genre_id = uuid7()
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides=_reader_override(GenreRelationsAssemblyError("broken")),
        ),
    ) as client:
        response = client.get(f"/api/v1/genres/{genre_id}/relations")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert body["message"] == "Не удалось загрузить материал."
    assert body["details"] is None
    assert isinstance(body["request_id"], str)
    assert body["request_id"]


def test_genre_relations_http_unexpected_failure_is_internal_error() -> None:
    genre_id = uuid7()
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides=_reader_override(RuntimeError("database details")),
        ),
    ) as client:
        response = client.get(f"/api/v1/genres/{genre_id}/relations")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert "database details" not in response.text
    assert isinstance(body["request_id"], str)
