from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import GroupSummary
from roots_of_rhythm.discovery.application.dto.groups import GroupListResponse

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


@runtime_checkable
class GroupListReader(Protocol):
    async def list(self) -> GroupListResponse: ...


class GroupListQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def list(self) -> GroupListResponse:
        async with self._uow_factory() as uow:
            groups = await uow.groups.list_published()
        return GroupListResponse(
            items=[GroupSummary(id=str(group.id), name=group.canonical_name) for group in groups],
        )
