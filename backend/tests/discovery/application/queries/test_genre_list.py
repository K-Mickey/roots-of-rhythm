from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.queries.genre_list import GenreListQuery
from roots_of_rhythm.music_catalog.domain import ClassificationContent, EditorialStatus, Genre
from tests.discovery.readers_stubs import StubGenreReader


def _genre(name: str, status: EditorialStatus) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Published definition."),
        editorial_status=status,
    )


@pytest.mark.asyncio
async def test_list_query_returns_names_in_input_order() -> None:
    swing = _genre("Swing", EditorialStatus.PUBLISHED)
    jazz = _genre("Jazz", EditorialStatus.PUBLISHED)
    query = GenreListQuery(StubGenreReader(genres=(swing, jazz)))

    response = await query.list()

    assert [item.name for item in response.items] == ["Swing", "Jazz"]
    assert [item.id for item in response.items] == [str(swing.id), str(jazz.id)]


@pytest.mark.asyncio
async def test_list_query_returns_empty_items_when_reader_is_empty() -> None:
    query = GenreListQuery(StubGenreReader(genres=()))

    response = await query.list()

    assert response.items == []
