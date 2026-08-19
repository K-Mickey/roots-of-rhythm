from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.performer_list import PerformerListQuery
from roots_of_rhythm.people_catalog.domain import EditorialStatus, Person, PersonContent
from tests.people_catalog.fakes import FakePeopleCatalogUnitOfWork


def _person(name: str, status: EditorialStatus) -> Person:
    return Person.create(uuid7(), PersonContent.create(name), editorial_status=status)


@pytest.mark.asyncio
async def test_performer_list_returns_only_published_people_in_canonical_order() -> None:
    louis = _person("Louis Armstrong", EditorialStatus.PUBLISHED)
    charlie = _person("Charlie Parker", EditorialStatus.PUBLISHED)
    draft = _person("Draft Person", EditorialStatus.DRAFT)
    archived = _person("Archived Person", EditorialStatus.ARCHIVED)
    query = PerformerListQuery(
        lambda: FakePeopleCatalogUnitOfWork(
            {person.id: person for person in (louis, charlie, draft, archived)},
        ),
    )

    response = await query.list()

    assert [(item.id, item.name) for item in response.items] == [
        (str(charlie.id), "Charlie Parker"),
        (str(louis.id), "Louis Armstrong"),
    ]


@pytest.mark.asyncio
async def test_performer_list_empty_is_success() -> None:
    query = PerformerListQuery(lambda: FakePeopleCatalogUnitOfWork({}))

    response = await query.list()

    assert response.items == []
