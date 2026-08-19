from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from types import TracebackType
    from uuid import UUID

    from roots_of_rhythm.people_catalog.domain import Person


class PersonRepository(Protocol):
    async def add(self, person: Person) -> None: ...

    async def get(self, person_id: UUID) -> Person | None: ...

    async def get_published(self, person_id: UUID) -> Person | None: ...

    async def list_published(self) -> list[Person]: ...

    async def save(self, person: Person) -> None: ...

    async def mark_deleted(self, person_id: UUID) -> None: ...


class PeopleCatalogUnitOfWork(Protocol):
    persons: PersonRepository

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
