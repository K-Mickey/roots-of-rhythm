from typing import TYPE_CHECKING

import pytest
from litestar.testing import TestClient

from roots_of_rhythm.config import Settings
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.seed import corpus as data

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


async def test_group_list_integration_returns_seeded_names_in_order(seeded_engine: AsyncEngine) -> None:
    database_url = seeded_engine.url.render_as_string(hide_password=False)
    with TestClient(app=create_app(Settings(database_url=database_url))) as client:
        response = client.get("/api/v1/groups")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"id": str(data.BENNY_GOODMAN_ORCHESTRA_ID), "name": "Benny Goodman Orchestra"},
            {"id": str(data.CHARLIE_PARKER_QUINTET_ID), "name": "Charlie Parker Quintet"},
            {"id": str(data.COUNT_BASIE_ORCHESTRA_ID), "name": "Count Basie Orchestra"},
            {"id": str(data.TYMPANY_FIVE_ID), "name": "Tympany Five"},
        ]
    }
