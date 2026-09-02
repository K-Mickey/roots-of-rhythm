from typing import TYPE_CHECKING

import pytest
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork

from roots_of_rhythm.music_catalog.application import MusicalWorkService
from roots_of_rhythm.music_catalog.domain import MusicalWork, WorkContent

if TYPE_CHECKING:
    from uuid import UUID


@pytest.mark.asyncio
async def test_musical_work_service_allows_duplicate_titles_and_publishes_both() -> None:
    works: dict[UUID, MusicalWork] = {}
    service = MusicalWorkService(lambda: FakeMusicCatalogUnitOfWork({}, works=works))
    content = WorkContent.create("Sixteen Tons", provenance="Editorial seed.")

    first = await service.create(content)
    second = await service.create(content)
    first = await service.publish(first.id)
    second = await service.publish(second.id)

    assert first.id != second.id
    assert first.is_published
    assert second.is_published
    assert [work.canonical_title for work in works.values()] == [
        "Sixteen Tons",
        "Sixteen Tons",
    ]
