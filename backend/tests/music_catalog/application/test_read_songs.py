from uuid import uuid7

import pytest
from tests.music_catalog.fakes import FakeMusicalWorkRepository
from tests.support.scopes import fake_transaction_scope

from roots_of_rhythm.music_catalog.application.read_services.songs import SongListReadService
from roots_of_rhythm.music_catalog.domain import EditorialStatus, MusicalWork, WorkContent


def _work(title: str, status: EditorialStatus = EditorialStatus.PUBLISHED) -> MusicalWork:
    return MusicalWork.create(
        uuid7(),
        WorkContent.create(title, provenance="Editorial review."),
        editorial_status=status,
    )


@pytest.mark.asyncio
async def test_song_list_read_service_lists_published_works_in_order() -> None:
    sixteen = _work("Sixteen Tons")
    ornithology = _work("Ornithology")
    draft = _work("Draft Song", EditorialStatus.DRAFT)
    repo = FakeMusicalWorkRepository({w.id: w for w in (sixteen, ornithology, draft)})
    service = SongListReadService(fake_transaction_scope(), lambda _t: repo)

    result = await service.list_published_works()

    assert [item.canonical_title for item in result] == ["Ornithology", "Sixteen Tons"]


@pytest.mark.asyncio
async def test_song_list_read_service_empty() -> None:
    service = SongListReadService(fake_transaction_scope(), lambda _t: FakeMusicalWorkRepository({}))

    assert await service.list_published_works() == ()
