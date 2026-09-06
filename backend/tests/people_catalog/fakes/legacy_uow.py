from typing import TYPE_CHECKING, Self

from tests.people_catalog.fakes.persons import FakePersonRepository

if TYPE_CHECKING:
    from types import TracebackType
    from uuid import UUID

    from roots_of_rhythm.people_catalog.application.ports import PersonRepository
    from roots_of_rhythm.people_catalog.domain import Person


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
