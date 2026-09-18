from typing import TYPE_CHECKING
from uuid import uuid7

from roots_of_rhythm.people_catalog.domain import Person, PersonAlreadyExistsError, PersonNotFound
from tests.people_catalog.support.fake_repository import FakePersonRepository
from tests.support.uow import FakeUnitOfWork

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.application.ports import UnitOfWork
    from roots_of_rhythm.people_catalog.application import PersonRepository
    from roots_of_rhythm.people_catalog.domain import PersonContent


class FakePersonService:
    def __init__(
        self,
        persons: tuple[Person, ...] = (),
    ) -> None:
        self._persons: dict[UUID, Person] = {person.id: person for person in persons}
        self._uow: UnitOfWork = FakeUnitOfWork()
        self._person_repository: PersonRepository = FakePersonRepository({})

    async def get_published_by_ids(self, person_ids: Collection[UUID]) -> tuple[Person, ...]:
        wanted = set(person_ids)
        return tuple(person for person in self._persons.values() if person.id in wanted and person.is_published)

    async def get_published(self, person_id: UUID) -> Person | None:
        person = self._persons.get(person_id)
        return person if person is not None and person.is_published else None

    async def list_published(self) -> tuple[Person, ...]:
        return tuple(
            sorted(
                (person for person in self._persons.values() if person.is_published),
                key=lambda person: person.canonical_name,
            )
        )

    async def create(self, content: PersonContent, *, person_id: UUID | None = None) -> Person:
        person = Person.create(person_id or uuid7(), content)
        if person.id in self._persons:
            raise PersonAlreadyExistsError(person.id)
        self._persons[person.id] = person
        return person

    async def replace_content(self, person_id: UUID, content: PersonContent) -> Person:
        person = self._persons.get(person_id)
        if person is None:
            raise PersonNotFound(str(person_id))
        updated = person.replace_content(content)
        self._persons[person_id] = updated
        return updated

    async def publish(self, person_id: UUID) -> Person:
        person = self._persons.get(person_id)
        if person is None:
            raise PersonNotFound(str(person_id))
        updated = person.publish()
        self._persons[person_id] = updated
        return updated

    async def archive(self, person_id: UUID) -> Person:
        person = self._persons.get(person_id)
        if person is None:
            raise PersonNotFound(str(person_id))
        updated = person.archive()
        self._persons[person_id] = updated
        return updated
