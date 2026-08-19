from typing import TYPE_CHECKING, Self

from roots_of_rhythm.people_catalog.domain import EditorialStatus

if TYPE_CHECKING:
    from types import TracebackType
    from uuid import UUID

    from roots_of_rhythm.people_catalog.application.ports import PersonRepository
    from roots_of_rhythm.people_catalog.domain import Person


class FakePersonRepository:
    def __init__(self, persons: dict[UUID, Person]) -> None:
        self._persons = persons

    async def add(self, person: Person) -> None:
        self._persons[person.id] = person

    async def get(self, person_id: UUID, *, for_update: bool = False) -> Person | None:
        return self._persons.get(person_id)

    async def get_published(self, person_id: UUID, *, for_update: bool = False) -> Person | None:
        person = self._persons.get(person_id)
        return person if person is not None and person.editorial_status is EditorialStatus.PUBLISHED else None

    async def list_published(self) -> list[Person]:
        return sorted(
            (person for person in self._persons.values() if person.editorial_status is EditorialStatus.PUBLISHED),
            key=lambda person: person.canonical_name,
        )

    async def save(self, person: Person) -> None:
        if person.id not in self._persons:
            raise LookupError(str(person.id))
        self._persons[person.id] = person

    async def mark_deleted(self, person_id: UUID) -> None:
        self._persons.pop(person_id, None)


class FakePeopleCatalogUnitOfWork:
    def __init__(self, persons: dict[UUID, Person]) -> None:
        self.persons: PersonRepository = FakePersonRepository(persons)
        self.commits = 0
        self.rollbacks = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.rollbacks += 1

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1
