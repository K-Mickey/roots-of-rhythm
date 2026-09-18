import pytest

from tests.support.test_client import create_client

pytestmark = pytest.mark.integration


def test_readiness_with_postgresql() -> None:
    with create_client() as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
