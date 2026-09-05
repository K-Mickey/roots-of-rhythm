from uuid import uuid7

import pytest
from tests.music_catalog.fakes import FakeGenreRepository
from tests.support.scopes import fake_transaction_scope

from roots_of_rhythm.music_catalog.application.read_services.genres import GenreReadService
from roots_of_rhythm.music_catalog.domain import ClassificationContent, EditorialStatus, Genre


def _genre(name: str, status: EditorialStatus = EditorialStatus.PUBLISHED) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Published definition."),
        editorial_status=status,
    )


@pytest.mark.asyncio
async def test_genre_read_service_lists_published_in_order() -> None:
    swing = _genre("Swing")
    jazz = _genre("Jazz")
    draft = _genre("Drafty", EditorialStatus.DRAFT)
    repo = FakeGenreRepository({swing.id: swing, jazz.id: jazz, draft.id: draft})
    service = GenreReadService(fake_transaction_scope(), lambda _t: repo)

    result = await service.list_published()

    assert [item.content.canonical_name for item in result] == ["Jazz", "Swing"]


@pytest.mark.asyncio
async def test_genre_read_service_get_published_hides_unpublished() -> None:
    draft = _genre("Drafty", EditorialStatus.DRAFT)
    hidden = _genre("Hidden", EditorialStatus.ARCHIVED)
    swing = _genre("Swing")
    repo = FakeGenreRepository({swing.id: swing, draft.id: draft, hidden.id: hidden})
    service = GenreReadService(fake_transaction_scope(), lambda _t: repo)

    assert (await service.get_published(swing.id)) is swing
    assert await service.get_published(draft.id) is None
    assert await service.get_published(hidden.id) is None
    assert await service.get_published(uuid7()) is None


@pytest.mark.asyncio
async def test_genre_read_service_get_published_by_ids_filters_and_empty() -> None:
    swing = _genre("Swing")
    draft = _genre("Drafty", EditorialStatus.DRAFT)
    repo = FakeGenreRepository({swing.id: swing, draft.id: draft})
    service = GenreReadService(fake_transaction_scope(), lambda _t: repo)

    assert await service.get_published_by_ids({swing.id, draft.id}) == {swing.id: swing}
    assert await service.get_published_by_ids(set()) == {}
