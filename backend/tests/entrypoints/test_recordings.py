from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from litestar.di import Provide
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.discovery.application.dto import RecordingOverviewResponse, SongPeriodView
from roots_of_rhythm.discovery.application.errors import RecordingOverviewNotFound
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.entrypoints.dependencies import RECORDING_OVERVIEW_READER_DEPENDENCY

if TYPE_CHECKING:
    from litestar import Litestar


class StubReader:
    def __init__(self, result: RecordingOverviewResponse | Exception) -> None:
        self.result = result

    async def get(self, _recording_id: UUID) -> RecordingOverviewResponse:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _client(reader: StubReader) -> "TestClient[Litestar]":
    return TestClient(
        app=create_app(
            Settings(database_url="postgresql+psycopg://roots:roots@127.0.0.1:1/missing?connect_timeout=1"),
            dependency_overrides={
                RECORDING_OVERVIEW_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        )
    )


def test_recording_overview_http_returns_public_shape() -> None:
    recording_id = uuid7()
    reader = StubReader(
        RecordingOverviewResponse(
            str(recording_id), "Take Five", SongPeriodView(None, None), None, None, None, [], [], [], [], None, []
        )
    )
    with _client(reader) as client:
        response = client.get(f"/api/v1/recordings/{recording_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Take Five"
    assert response.json()["first_release_date"] is None


def test_recording_overview_http_hides_malformed_and_nonpublic_ids() -> None:
    with _client(StubReader(RecordingOverviewNotFound("missing"))) as client:
        malformed = client.get("/api/v1/recordings/nope")
        missing = client.get(f"/api/v1/recordings/{uuid7()}")
    assert malformed.status_code == missing.status_code == 404
    assert malformed.json()["code"] == missing.json()["code"] == "RECORDING_NOT_FOUND"


def test_recording_overview_http_maps_assembly_failure() -> None:
    with _client(StubReader(RuntimeError("boom"))) as client:
        response = client.get(f"/api/v1/recordings/{uuid7()}")
    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"
