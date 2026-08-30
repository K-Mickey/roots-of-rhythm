from uuid import uuid7

from litestar.di import Provide
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.discovery.application.dto.common import (
    GenreSummary,
    GroupSummary,
    TemporalBoundView,
)
from roots_of_rhythm.discovery.application.dto.groups import (
    GroupListResponse,
    GroupMemberView,
    GroupOverviewResponse,
    GroupPeriodView,
)
from roots_of_rhythm.discovery.application.errors.groups import GroupOverviewNotFound
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.entrypoints.dependencies import (
    GROUP_LIST_READER_DEPENDENCY,
    GROUP_OVERVIEW_READER_DEPENDENCY,
)
from roots_of_rhythm.music_catalog.domain import TemporalPrecision
from tests.discovery.fakes import StubGroupListReader, StubGroupOverviewReader


def _settings() -> Settings:
    return Settings(database_url="postgresql+psycopg://roots:roots@127.0.0.1:1/missing?connect_timeout=1")


def test_group_list_http_returns_200_shape() -> None:
    reader = StubGroupListReader(
        GroupListResponse(items=[GroupSummary(id="group-1", name="Count Basie Orchestra")]),
    )
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                GROUP_LIST_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get("/api/v1/groups")

    assert response.status_code == 200
    assert response.json() == {"items": [{"id": "group-1", "name": "Count Basie Orchestra"}]}


def test_group_list_http_internal_error_does_not_use_group_not_found() -> None:
    reader = StubGroupListReader(RuntimeError("database unavailable"))
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                GROUP_LIST_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get("/api/v1/groups")

    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"


def test_group_overview_http_returns_all_public_fields() -> None:
    group_id = uuid7()
    reader = StubGroupOverviewReader(
        GroupOverviewResponse(
            id=str(group_id),
            name="Count Basie Orchestra",
            aliases=["Basie band"],
            description="A swing orchestra.",
            period=GroupPeriodView(
                start=TemporalBoundView(1935, TemporalPrecision.EXACT_YEAR),
                end=TemporalBoundView(1950, TemporalPrecision.CIRCA_YEAR),
            ),
            primary_image=None,
            genres=[GenreSummary(id="genre-1", name="Swing")],
            members=[
                GroupMemberView(
                    id="person-1",
                    name="Count Basie",
                    period=GroupPeriodView(
                        start=TemporalBoundView(1935, TemporalPrecision.EXACT_YEAR),
                        end=TemporalBoundView(1950, TemporalPrecision.CIRCA_YEAR),
                    ),
                    roles_or_instruments=["piano", "bandleader"],
                ),
            ],
        ),
    )
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                GROUP_OVERVIEW_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get(f"/api/v1/groups/{group_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(group_id),
        "name": "Count Basie Orchestra",
        "aliases": ["Basie band"],
        "description": "A swing orchestra.",
        "period": {
            "start": {"year": 1935, "precision": "exact_year"},
            "end": {"year": 1950, "precision": "circa_year"},
        },
        "primary_image": None,
        "genres": [{"id": "genre-1", "name": "Swing"}],
        "members": [
            {
                "id": "person-1",
                "name": "Count Basie",
                "period": {
                    "start": {"year": 1935, "precision": "exact_year"},
                    "end": {"year": 1950, "precision": "circa_year"},
                },
                "roles_or_instruments": ["piano", "bandleader"],
            },
        ],
    }


def test_group_overview_http_malformed_id_is_not_found() -> None:
    reader = StubGroupOverviewReader(GroupOverviewNotFound("not-a-uuid"))
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                GROUP_OVERVIEW_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get("/api/v1/groups/not-a-uuid")

    assert response.status_code == 404
    assert response.json()["code"] == "GROUP_NOT_FOUND"


def test_group_overview_http_unpublished_id_is_not_found() -> None:
    group_id = uuid7()
    reader = StubGroupOverviewReader(GroupOverviewNotFound(str(group_id)))
    with TestClient(
        app=create_app(
            _settings(),
            dependency_overrides={
                GROUP_OVERVIEW_READER_DEPENDENCY: Provide(lambda: reader, sync_to_thread=False),
            },
        ),
    ) as client:
        response = client.get(f"/api/v1/groups/{group_id}")

    assert response.status_code == 404
    assert response.json()["code"] == "GROUP_NOT_FOUND"
