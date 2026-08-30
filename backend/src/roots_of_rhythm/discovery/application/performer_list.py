from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import PerformerSummary
from roots_of_rhythm.discovery.application.dto.performers import PerformerListResponse

if TYPE_CHECKING:
    from roots_of_rhythm.people_catalog.application.ports import PeopleCatalogUnitOfWork

type UnitOfWorkFactory = Callable[[], PeopleCatalogUnitOfWork]


@runtime_checkable
class PerformerListReader(Protocol):
    async def list(self) -> PerformerListResponse: ...


class PerformerListQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def list(self) -> PerformerListResponse:
        async with self._uow_factory() as uow:
            persons = await uow.persons.list_published()
        return PerformerListResponse(
            items=[PerformerSummary(id=str(person.id), name=person.canonical_name) for person in persons],
        )
