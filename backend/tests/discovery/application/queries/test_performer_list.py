from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.queries.performer_list import PerformerListQuery
from roots_of_rhythm.people_catalog.domain import EditorialStatus, Person, PersonContent
from tests.people_catalog.support.fake_service import FakePersonService


def _person(name: str, status: EditorialStatus) -> Person:
    return Person.create(uuid7(), PersonContent.create(name), editorial_status=status)


@pytest.mark.asyncio
async def test_performer_list_query_maps_input_order() -> None:
    louis = _person("Louis Armstrong", EditorialStatus.PUBLISHED)
    charlie = _person("Charlie Parker", EditorialStatus.PUBLISHED)
    query = PerformerListQuery(FakePersonService((louis, charlie)))

    response = await query.list()

    assert [item.name for item in response.items] == ["Charlie Parker", "Louis Armstrong"]


@pytest.mark.asyncio
async def test_performer_list_query_returns_empty_items_when_reader_is_empty() -> None:
    query = PerformerListQuery(FakePersonService())

    response = await query.list()

    assert response.items == []
