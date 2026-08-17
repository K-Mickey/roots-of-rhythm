from os import environ

import pytest
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings, settings
from roots_of_rhythm.entrypoints.api import create_app

pytestmark = pytest.mark.integration


def test_readiness_with_postgresql() -> None:
    test_settings = Settings(database_url=environ.get("TEST_DATABASE_URL", settings.database_url))
    with TestClient(app=create_app(test_settings)) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
