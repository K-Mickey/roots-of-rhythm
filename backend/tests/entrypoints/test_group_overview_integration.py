from typing import TYPE_CHECKING

import pytest

from roots_of_rhythm.seed import genre_knowledge as genre_data
from roots_of_rhythm.seed import people_and_groups as artist_data

if TYPE_CHECKING:
    from litestar import Litestar
    from litestar.testing import TestClient

pytestmark = pytest.mark.integration


async def test_group_overview_integration_returns_seeded_basie_orchestra(seeded_client: TestClient[Litestar]) -> None:
    with seeded_client as client:
        response = client.get(f"/api/v1/groups/{artist_data.COUNT_BASIE_ORCHESTRA_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(artist_data.COUNT_BASIE_ORCHESTRA_ID)
    assert body["name"] == "Count Basie Orchestra"
    assert body["aliases"] == []
    assert body["description"] is None
    assert body["period"] == {"start": None, "end": None}
    assert body["primary_image"] is None
    assert body["genres"] == [{"id": str(genre_data.SWING_ID), "name": "Swing"}]
    assert body["members"] == [
        {
            "id": str(artist_data.COUNT_BASIE_ID),
            "name": "Count Basie",
            "period": {
                "start": {"year": 1935, "precision": "exact_year"},
                "end": {"year": 1950, "precision": "circa_year"},
            },
            "roles_or_instruments": ["piano", "bandleader"],
        },
    ]
