from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
import sqlalchemy as sa

from roots_of_rhythm.people_catalog.domain import Person, PersonContent
from roots_of_rhythm.people_catalog.infrastructure.person_repository import PgPersonRepository
from tests.people_catalog.support.helpers import create_person

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.application.ports import DbAccessor
    from roots_of_rhythm.people_catalog.application import PersonRepository


@pytest.fixture
def repository(database: DbAccessor) -> PersonRepository:
    # use Person Repository for checking Base Repository because need Alchemy Model for class work
    return PgPersonRepository(database)


async def get_person(repo: PersonRepository, id_: UUID) -> Person | None:
    query = sa.select(repo.model).where(repo.model.id == id_)  # type: ignore[attr-defined]
    result = await repo._db.scalar_one_or_none(query)  # type: ignore[attr-defined]
    return repo.to_domain(result) if result else None  # type: ignore[attr-defined]


def update_person(person_id: UUID, name: str) -> Person:
    return Person.create(person_id, PersonContent.create(name))


async def test_add(repository: PersonRepository) -> None:
    person = create_person("Sam")
    await repository.add(person)
    created = await get_person(repository, person.id)
    assert created
    assert person.id == created.id
    assert person.canonical_name == created.canonical_name


async def test_get(repository: PersonRepository) -> None:
    person = create_person("Sam")
    await repository.add(person)
    created = await repository.get(person.id)
    assert created
    assert created.id == person.id


async def test_get_empty(repository: PersonRepository) -> None:
    assert await repository.get(uuid7()) is None


async def test_mark_deleted(repository: PersonRepository) -> None:
    person = create_person("Sam")
    await repository.add(person)
    assert await repository.get(person.id) is not None
    await repository.mark_deleted(person.id)
    assert await repository.get(person.id) is None
    assert await get_person(repository, person.id) is not None


async def test_mark_deleted_independent(repository: PersonRepository) -> None:
    first = create_person("Sam")
    await repository.add(first)
    second = create_person("Dean")
    await repository.add(second)
    await repository.mark_deleted(first.id)
    assert await repository.get(first.id) is None
    assert await repository.get(second.id) is not None


async def test_save(repository: PersonRepository) -> None:
    person = create_person("Sam")
    await repository.add(person)
    new_content = update_person(person.id, name="Dean")
    updated = await repository.save(new_content)
    assert person.id == updated.id
    assert updated.canonical_name == "Dean"


async def test_save_empty(repository: PersonRepository) -> None:
    person = create_person("Sam")
    with pytest.raises(LookupError):
        await repository.save(person)


async def test_save_deleted(repository: PersonRepository) -> None:
    person = create_person("Sam")
    await repository.add(person)
    await repository.mark_deleted(person.id)
    with pytest.raises(LookupError):
        await repository.save(person)


async def test_save_independent(repository: PersonRepository) -> None:
    first = create_person("Sam")
    await repository.add(first)
    second = create_person("Dean")
    await repository.add(second)
    new_content = update_person(first.id, name="Aaron")
    updated = await repository.save(new_content)
    assert updated.canonical_name == "Aaron"
    not_updated = await repository.get(second.id)
    assert not_updated
    assert not_updated.canonical_name == "Dean"
