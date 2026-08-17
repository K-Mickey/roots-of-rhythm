from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.entrypoints.api import create_app


def test_liveness_does_not_require_database() -> None:
    settings = Settings(database_url="postgresql+psycopg://roots:roots@127.0.0.1:1/missing?connect_timeout=1")
    with TestClient(app=create_app(settings)) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_is_unavailable_without_database() -> None:
    settings = Settings(database_url="postgresql+psycopg://roots:roots@127.0.0.1:1/missing?connect_timeout=1")
    with TestClient(app=create_app(settings)) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
