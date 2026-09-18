from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from tests.people_catalog.support.helpers import create_person

from roots_of_rhythm.application.errors import UniqueConstraintViolation
from roots_of_rhythm.people_catalog.domain import EditorialStatus

if TYPE_CHECKING:
    from roots_of_rhythm.people_catalog.application import PersonRepository
    from roots_of_rhythm.people_catalog.domain import Person

pytestmark = pytest.mark.integration

PERSON_INFO = (
    ("Sam", EditorialStatus.PUBLISHED),
    ("Kris", EditorialStatus.PUBLISHED),
    ("Aaron", EditorialStatus.DRAFT),
    ("Baron", EditorialStatus.ARCHIVED),
    ("Smith", EditorialStatus.IN_REVIEW),
    ("Kenny", EditorialStatus.PUBLISHED),
)


async def create_persons(repo: PersonRepository) -> list[Person]:
    persons = []
    for name, status in PERSON_INFO:
        person = await repo.add(create_person(name, status=status))
        persons.append(person)
    await repo.mark_deleted(persons[-1].id)
    return persons


async def test_add(person_repository: PersonRepository) -> None:
    person = create_person("Sam")
    await person_repository.add(person)
    added = await person_repository.get(person.id)
    assert added
    assert person.id == added.id
    assert added.canonical_name == "Sam"


async def test_add_many(person_repository: PersonRepository) -> None:
    for name, _ in PERSON_INFO:
        await person_repository.add(create_person(name))
    published = await person_repository.list_published()
    assert len(published) == 6


async def test_add_with_error(person_repository: PersonRepository) -> None:
    person = create_person("Sam")
    await person_repository.add(person)
    with pytest.raises(UniqueConstraintViolation):
        await person_repository.add(person)


async def test_add_after_remove(person_repository: PersonRepository) -> None:
    person = create_person("Sam")
    await person_repository.add(person)
    await person_repository.mark_deleted(person.id)
    assert await person_repository.get(person.id) is None

    person = create_person("Sam")
    await person_repository.add(person)
    assert await person_repository.get(person.id) is not None


async def test_list_published_empty(person_repository: PersonRepository) -> None:
    created = await person_repository.list_published()
    assert created is not None
    assert len(created) == 0


async def test_list_published(person_repository: PersonRepository) -> None:
    persons = await create_persons(person_repository)
    published = await person_repository.list_published()
    assert len(published) == 2
    assert [p.id for p in published] == [persons[1].id, persons[0].id]
    for person in persons[2:5]:
        created = await person_repository.get(person.id)
        assert created is not None


async def test_get_published(person_repository: PersonRepository) -> None:
    person = await person_repository.add(create_person("Sam"))
    created = await person_repository.get_published(person.id)
    assert created
    assert person.id == created.id
    assert created.is_published


async def test_get_published_not_exist(person_repository: PersonRepository) -> None:
    not_created = await person_repository.get_published(uuid7())
    assert not_created is None


async def test_get_published_deleted(person_repository: PersonRepository) -> None:
    person = await person_repository.add(create_person("Kenny"))
    await person_repository.mark_deleted(person.id)
    created = await person_repository.get_published(person.id)
    assert created is None


@pytest.mark.parametrize("status", (EditorialStatus.IN_REVIEW, EditorialStatus.ARCHIVED, EditorialStatus.DRAFT))
async def test_get_not_published(person_repository: PersonRepository, status: EditorialStatus) -> None:
    person = await person_repository.add(create_person("Sam", status=status))
    created = await person_repository.get_published(person.id)
    assert created is None


async def test_get_published_empty(person_repository: PersonRepository) -> None:
    created = await person_repository.get_published_by_ids([])
    assert created is not None
    assert len(created) == 0


async def test_get_published_by_ids(person_repository: PersonRepository) -> None:
    persons = await create_persons(person_repository)
    ids = [p.id for p in persons] + [persons[0].id]
    created = await person_repository.get_published_by_ids(ids)
    assert len(created) == 2
    assert {p for p in created.values()} == set(persons[:2])  # noqa: C416
