from typing import TYPE_CHECKING

import pytest

from roots_of_rhythm.seed import genre_knowledge as genre_data

if TYPE_CHECKING:
    from litestar import Litestar
    from litestar.testing import TestClient

pytestmark = pytest.mark.integration


async def test_genre_list_integration_returns_seeded_names_in_order(seeded_client: TestClient[Litestar]) -> None:
    with seeded_client as client:
        response = client.get("/api/v1/genres")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"id": str(genre_data.COUNTRY_ID), "name": "Country"},
            {"id": str(genre_data.JAZZ_ID), "name": "Jazz"},
            {"id": str(genre_data.JUMP_BLUES_ID), "name": "Jump Blues"},
            {"id": str(genre_data.RHYTHM_AND_BLUES_ID), "name": "Rhythm and Blues"},
            {"id": str(genre_data.SWING_ID), "name": "Swing"},
        ]
    }
