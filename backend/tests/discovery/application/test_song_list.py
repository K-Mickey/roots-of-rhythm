from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.song_list import SongListQuery
from roots_of_rhythm.music_catalog.domain import EditorialStatus, MusicalWork, WorkContent
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork


def _work(title: str, status: EditorialStatus) -> MusicalWork:
    return MusicalWork.create(
        uuid7(),
        WorkContent.create(title, provenance="Editorial review."),
        editorial_status=status,
    )


@pytest.mark.asyncio
async def test_song_list_returns_only_published_works_in_canonical_order() -> None:
    sixteen_tons = _work("Sixteen Tons", EditorialStatus.PUBLISHED)
    ornithology = _work("Ornithology", EditorialStatus.PUBLISHED)
    draft = _work("Draft Song", EditorialStatus.DRAFT)
    archived = _work("Archived Song", EditorialStatus.ARCHIVED)
    query = SongListQuery(
        lambda: FakeMusicCatalogUnitOfWork(
            {},
            works={work.id: work for work in (sixteen_tons, ornithology, draft, archived)},
        ),
    )

    response = await query.list()

    assert [(item.id, item.name) for item in response.items] == [
        (str(ornithology.id), "Ornithology"),
        (str(sixteen_tons.id), "Sixteen Tons"),
    ]


@pytest.mark.asyncio
async def test_song_list_empty_is_success() -> None:
    query = SongListQuery(lambda: FakeMusicCatalogUnitOfWork({}, works={}))

    response = await query.list()

    assert response.items == []
