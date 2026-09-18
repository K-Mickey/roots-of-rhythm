from typing import TYPE_CHECKING

import pytest

from roots_of_rhythm.seed import people_and_groups as artist_data

if TYPE_CHECKING:
    from litestar import Litestar
    from litestar.testing import TestClient

pytestmark = pytest.mark.integration


async def test_group_list_integration_returns_seeded_names_in_order(seeded_client: TestClient[Litestar]) -> None:
    with seeded_client as client:
        response = client.get("/api/v1/groups")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"id": str(artist_data.BENNY_GOODMAN_ORCHESTRA_ID), "name": "Benny Goodman Orchestra"},
            {"id": str(artist_data.CHARLIE_PARKER_QUINTET_ID), "name": "Charlie Parker Quintet"},
            {"id": str(artist_data.COUNT_BASIE_ORCHESTRA_ID), "name": "Count Basie Orchestra"},
            {"id": str(artist_data.TYMPANY_FIVE_ID), "name": "Tympany Five"},
        ]
    }
