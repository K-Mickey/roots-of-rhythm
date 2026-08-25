from typing import TYPE_CHECKING

import pytest
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork

from roots_of_rhythm.music_catalog.application import GroupService
from roots_of_rhythm.music_catalog.domain import EditorialStatus, Group, GroupContent

if TYPE_CHECKING:
    from uuid import UUID


@pytest.mark.asyncio
async def test_group_service_allows_duplicate_canonical_names_and_publishes_both() -> None:
    groups: dict[UUID, Group] = {}
    service = GroupService(lambda: FakeMusicCatalogUnitOfWork({}, groups=groups))

    first = await service.create(GroupContent.create("Count Basie Orchestra"))
    second = await service.create(GroupContent.create("Count Basie Orchestra"))
    first = await service.publish(first.id)
    second = await service.publish(second.id)

    assert first.id != second.id
    assert first.editorial_status is second.editorial_status is EditorialStatus.PUBLISHED
    assert [group.canonical_name for group in groups.values()] == [
        "Count Basie Orchestra",
        "Count Basie Orchestra",
    ]
