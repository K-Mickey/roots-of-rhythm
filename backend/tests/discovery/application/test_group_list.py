from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.group_list import GroupListQuery
from roots_of_rhythm.music_catalog.domain import EditorialStatus, Group, GroupContent
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork


def _group(name: str, status: EditorialStatus) -> Group:
    return Group.create(uuid7(), GroupContent.create(name), editorial_status=status)


@pytest.mark.asyncio
async def test_group_list_returns_only_published_groups_in_canonical_order() -> None:
    benny = _group("Benny Goodman Orchestra", EditorialStatus.PUBLISHED)
    charlie = _group("Charlie Parker Quintet", EditorialStatus.PUBLISHED)
    draft = _group("Draft Group", EditorialStatus.DRAFT)
    archived = _group("Archived Group", EditorialStatus.ARCHIVED)
    query = GroupListQuery(
        lambda: FakeMusicCatalogUnitOfWork(
            {},
            groups={group.id: group for group in (benny, charlie, draft, archived)},
        ),
    )

    response = await query.list()

    assert [(item.id, item.name) for item in response.items] == [
        (str(benny.id), "Benny Goodman Orchestra"),
        (str(charlie.id), "Charlie Parker Quintet"),
    ]


@pytest.mark.asyncio
async def test_group_list_empty_is_success() -> None:
    query = GroupListQuery(lambda: FakeMusicCatalogUnitOfWork({}))

    response = await query.list()

    assert response.items == []
