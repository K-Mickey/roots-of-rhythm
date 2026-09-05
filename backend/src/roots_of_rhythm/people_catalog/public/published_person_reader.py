from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.people_catalog.domain import Person


@dataclass(frozen=True, slots=True)
class PublishedPeopleReadData:
    persons: tuple[Person, ...]


class PublishedPeopleReader(Protocol):
    async def get_published_by_ids(self, person_ids: Collection[UUID]) -> PublishedPeopleReadData: ...

    async def get_published(self, person_id: UUID) -> Person | None: ...

    async def list_published(self) -> tuple[Person, ...]: ...
