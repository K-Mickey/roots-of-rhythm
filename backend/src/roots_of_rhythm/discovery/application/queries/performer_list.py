from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import PerformerSummary
from roots_of_rhythm.discovery.application.dto.performers import PerformerListResponse

if TYPE_CHECKING:
    from roots_of_rhythm.people_catalog.public.published_person import PeopleCatalog


@runtime_checkable
class PerformerListReader(Protocol):
    async def list(self) -> PerformerListResponse: ...


class PerformerListQuery:
    def __init__(self, people: PeopleCatalog) -> None:
        self._people = people

    async def list(self) -> PerformerListResponse:
        persons = await self._people.list_published()
        return PerformerListResponse(
            items=[PerformerSummary(id=str(person.id), name=person.canonical_name) for person in persons],
        )
