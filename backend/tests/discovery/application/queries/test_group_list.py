from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.queries.group_list import GroupListQuery
from roots_of_rhythm.music_catalog.domain import EditorialStatus, Group, GroupContent
from tests.discovery.readers_stubs import StubGroupReader


def _group(name: str, status: EditorialStatus) -> Group:
    return Group.create(
        uuid7(),
        GroupContent.create(name),
        editorial_status=status,
    )


@pytest.mark.asyncio
async def test_group_list_query_maps_input_order() -> None:
    basie = _group("Count Basie Orchestra", EditorialStatus.PUBLISHED)
    zeta = _group("Zeta", EditorialStatus.PUBLISHED)
    query = GroupListQuery(StubGroupReader(groups=(basie, zeta)))

    response = await query.list()

    assert [item.name for item in response.items] == ["Count Basie Orchestra", "Zeta"]


@pytest.mark.asyncio
async def test_group_list_query_returns_empty_items_when_reader_is_empty() -> None:
    query = GroupListQuery(StubGroupReader(groups=()))

    response = await query.list()

    assert response.items == []
