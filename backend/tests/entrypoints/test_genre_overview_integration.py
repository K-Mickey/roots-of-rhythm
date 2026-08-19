from typing import TYPE_CHECKING

import pytest
from litestar.testing import TestClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

from roots_of_rhythm.config import Settings
from roots_of_rhythm.entrypoints.api import create_app
from roots_of_rhythm.seed import corpus as data

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


async def test_genre_overview_integration_returns_seeded_swing_in_one_select(seeded_engine: AsyncEngine) -> None:
    statements: list[str] = []

    def _count_statement(_conn: object, _cursor: object, statement: str, *_args: object, **_kwargs: object) -> None:
        statements.append(statement)

    event.listen(Engine, "before_cursor_execute", _count_statement)
    try:
        database_url = seeded_engine.url.render_as_string(hide_password=False)
        with TestClient(app=create_app(Settings(database_url=database_url))) as client:
            response = client.get(f"/api/v1/genres/{data.SWING_ID}")
    finally:
        event.remove(Engine, "before_cursor_execute", _count_statement)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(data.SWING_ID)
    assert body["name"] == "Swing"
    assert body["definition"] == data.SWING_CONTENT.definition
    assert body["primary_image"] is None
    assert body["characteristic_features"] == []
    selects = [statement for statement in statements if statement.lstrip().upper().startswith("SELECT")]
    assert len(selects) == 1
