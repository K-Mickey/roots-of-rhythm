from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import SongSummary
from roots_of_rhythm.discovery.application.dto.songs import SongListResponse

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


@runtime_checkable
class SongListReader(Protocol):
    async def list(self) -> SongListResponse: ...


class SongListQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def list(self) -> SongListResponse:
        async with self._uow_factory() as uow:
            works = await uow.works.list_published()
        return SongListResponse(
            items=[SongSummary(id=str(work.id), name=work.canonical_title) for work in works],
        )
