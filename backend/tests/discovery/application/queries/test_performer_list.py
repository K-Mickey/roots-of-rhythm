from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.queries.performer_list import PerformerListQuery
from roots_of_rhythm.people_catalog.domain import EditorialStatus, Person, PersonContent
from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReadData
from tests.discovery.readers_stubs import StubPublishedPeopleReader


def _person(name: str, status: EditorialStatus) -> Person:
    return Person.create(uuid7(), PersonContent.create(name), editorial_status=status)


@pytest.mark.asyncio
async def test_performer_list_query_maps_input_order() -> None:
    louis = _person("Louis Armstrong", EditorialStatus.PUBLISHED)
    charlie = _person("Charlie Parker", EditorialStatus.PUBLISHED)
    query = PerformerListQuery(StubPublishedPeopleReader(PublishedPeopleReadData(persons=(louis, charlie))))

    response = await query.list()

    assert [item.name for item in response.items] == ["Louis Armstrong", "Charlie Parker"]


@pytest.mark.asyncio
async def test_performer_list_query_returns_empty_items_when_reader_is_empty() -> None:
    query = PerformerListQuery(StubPublishedPeopleReader(PublishedPeopleReadData(persons=())))

    response = await query.list()

    assert response.items == []
