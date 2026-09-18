from typing import TYPE_CHECKING
from uuid import uuid7

import pytest

from roots_of_rhythm.people_catalog.application import PersonService
from roots_of_rhythm.people_catalog.domain import EditorialStatus, Person, PersonContent, PersonNotFound
from tests.people_catalog.support.fake_repository import FakePersonRepository
from tests.people_catalog.support.helpers import create_person
from tests.support.uow import FakeUnitOfWork

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.people_catalog.public import PeopleCatalog


def create_service(persons: dict[UUID, Person] | None = None) -> PeopleCatalog:
    if persons is None:
        persons = {}
    return PersonService(FakeUnitOfWork(), FakePersonRepository(persons))


async def test_person_service_allows_duplicate_canonical_names_and_publishes_both() -> None:
    persons: dict[UUID, Person] = {}
    service = create_service(persons)

    first = await service.create(PersonContent.create("John Smith"))
    second = await service.create(PersonContent.create("John Smith"))
    first = await service.publish(first.id)
    second = await service.publish(second.id)

    assert first.id != second.id
    assert first.is_published
    assert second.is_published
    assert [person.canonical_name for person in persons.values()] == ["John Smith", "John Smith"]


async def test_change_statuses() -> None:
    service = create_service()
    person = await service.create(PersonContent.create("John Smith"))
    assert person.is_draft
    person = await service.publish(person.id)
    assert person.is_published
    person = await service.archive(person.id)
    assert person.is_archived
    person = await service.publish(person.id)
    assert person.is_published


async def test_replace_content() -> None:
    persons: dict[UUID, Person] = {}
    service = create_service(persons)
    first = await service.create(PersonContent.create("John Smith"))
    await service.create(PersonContent.create("John Smith"))
    await service.replace_content(first.id, PersonContent.create("Joana Smith"))
    assert [person.canonical_name for person in persons.values()] == ["Joana Smith", "John Smith"]


async def test_replace_content_not_exist() -> None:
    persons: dict[UUID, Person] = {}
    service = create_service(persons)
    with pytest.raises(PersonNotFound):
        await service.replace_content(uuid7(), PersonContent.create("Joana Smith"))
    assert len(persons) == 0


async def test_persons_read_service_get_published_by_ids_filters_and_empty() -> None:
    louis = create_person("Louis Armstrong")
    draft = create_person("Hidden", EditorialStatus.DRAFT)
    service = create_service({louis.id: louis, draft.id: draft})

    result = await service.get_published_by_ids({louis.id, draft.id})

    assert {item.id for item in result} == {louis.id}
    assert await service.get_published_by_ids(set()) == ()


async def test_persons_read_service_get_published_hides_unpublished() -> None:
    louis = create_person("Louis Armstrong")
    draft = create_person("Hidden", EditorialStatus.DRAFT)
    service = create_service({louis.id: louis, draft.id: draft})

    assert (await service.get_published(louis.id)) is louis
    assert await service.get_published(draft.id) is None
    assert await service.get_published(uuid7()) is None


async def test_persons_read_service_list_published_in_order() -> None:
    louis = create_person("Louis Armstrong")
    charlie = create_person("Charlie Parker")
    draft = create_person("Draft", EditorialStatus.DRAFT)
    service = create_service({louis.id: louis, charlie.id: charlie, draft.id: draft})

    result = await service.list_published()

    assert [item.canonical_name for item in result] == ["Charlie Parker", "Louis Armstrong"]
