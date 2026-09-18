from typing import TYPE_CHECKING
from uuid import uuid7

from roots_of_rhythm.application.errors import UniqueConstraintViolation
from roots_of_rhythm.people_catalog.domain import Person, PersonAlreadyExistsError, PersonContent, PersonNotFound

if TYPE_CHECKING:
    from collections.abc import Callable, Collection
    from uuid import UUID

    from roots_of_rhythm.application.ports import UnitOfWork
    from roots_of_rhythm.people_catalog.application import PersonRepository


class PersonService:
    def __init__(self, uow: UnitOfWork, person_repository: PersonRepository) -> None:
        self._uow = uow
        self._person_repository = person_repository

    async def get_published_by_ids(self, person_ids: Collection[UUID]) -> tuple[Person, ...]:
        persons = await self._person_repository.get_published_by_ids(person_ids)
        return tuple(persons.values())

    async def get_published(self, person_id: UUID) -> Person | None:
        return await self._person_repository.get_published(person_id)

    async def list_published(self) -> tuple[Person, ...]:
        return await self._person_repository.list_published()

    async def create(self, content: PersonContent, *, person_id: UUID | None = None) -> Person:
        person = Person.create(person_id or uuid7(), content)
        try:
            return await self._person_repository.add(person)
        except UniqueConstraintViolation as error:
            raise PersonAlreadyExistsError(person.id) from error

    async def replace_content(self, person_id: UUID, content: PersonContent) -> Person:
        async with self._uow():
            person = await self._person_repository.get(person_id, for_update=True)
            if not person:
                raise PersonNotFound(str(person_id))
            updated = person.replace_content(content)
            return await self._save(updated)

    async def publish(self, person_id: UUID) -> Person:
        return await self._change_status(person_id, Person.publish)

    async def archive(self, person_id: UUID) -> Person:
        return await self._change_status(person_id, Person.archive)

    async def _change_status(self, person_id: UUID, transition: Callable[[Person], Person]) -> Person:
        async with self._uow():
            person = await self._person_repository.get(person_id, for_update=True)
            if not person:
                raise PersonNotFound(str(person_id))
            updated = transition(person)
            return await self._save(updated)

    async def _save(self, person: Person) -> Person:
        try:
            return await self._person_repository.save(person)
        except LookupError as exc:
            raise PersonNotFound(str(person.id)) from exc
