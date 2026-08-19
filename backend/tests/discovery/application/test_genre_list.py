from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.genre_list import GenreListQuery
from roots_of_rhythm.music_catalog.domain import ClassificationContent, EditorialStatus, Genre
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork


def _genre(name: str, status: EditorialStatus) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Published definition."),
        editorial_status=status,
    )


@pytest.mark.asyncio
async def test_list_query_returns_published_names_in_canonical_order() -> None:
    swing = _genre("Swing", EditorialStatus.PUBLISHED)
    jazz = _genre("Jazz", EditorialStatus.PUBLISHED)
    draft = _genre("Drafty", EditorialStatus.DRAFT)
    archived = _genre("Archived", EditorialStatus.ARCHIVED)
    query = GenreListQuery(
        lambda: FakeMusicCatalogUnitOfWork(
            {
                swing.id: swing,
                jazz.id: jazz,
                draft.id: draft,
                archived.id: archived,
            }
        )
    )

    response = await query.list()

    assert [item.name for item in response.items] == ["Jazz", "Swing"]
    assert [item.id for item in response.items] == [str(jazz.id), str(swing.id)]


@pytest.mark.asyncio
async def test_list_query_returns_empty_items_when_none_published() -> None:
    draft = _genre("Hidden", EditorialStatus.DRAFT)
    query = GenreListQuery(lambda: FakeMusicCatalogUnitOfWork({draft.id: draft}))

    response = await query.list()

    assert response.items == []
