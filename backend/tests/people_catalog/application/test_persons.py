from typing import TYPE_CHECKING

import pytest
from tests.people_catalog.fakes import FakePeopleCatalogUnitOfWork

from roots_of_rhythm.people_catalog.application import PersonService
from roots_of_rhythm.people_catalog.domain import EditorialStatus, Person, PersonContent

if TYPE_CHECKING:
    from uuid import UUID


@pytest.mark.asyncio
async def test_person_service_allows_duplicate_canonical_names_and_publishes_both() -> None:
    persons: dict[UUID, Person] = {}
    service = PersonService(lambda: FakePeopleCatalogUnitOfWork(persons))

    first = await service.create(PersonContent.create("John Smith"))
    second = await service.create(PersonContent.create("John Smith"))
    first = await service.publish(first.id)
    second = await service.publish(second.id)

    assert first.id != second.id
    assert first.editorial_status is second.editorial_status is EditorialStatus.PUBLISHED
    assert [person.canonical_name for person in persons.values()] == ["John Smith", "John Smith"]
