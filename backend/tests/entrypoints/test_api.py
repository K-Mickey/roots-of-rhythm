from tests.support.test_client import create_missing_client


def test_liveness_does_not_require_database() -> None:
    client = create_missing_client()
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_is_unavailable_without_database() -> None:
    client = create_missing_client()
    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
