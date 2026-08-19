from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto import GenreListResponse, GenreSummary

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


@runtime_checkable
class GenreListReader(Protocol):
    async def list(self) -> GenreListResponse: ...


class GenreListQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def list(self) -> GenreListResponse:
        async with self._uow_factory() as uow:
            genres = await uow.genres.list_published()
        return GenreListResponse(
            items=[GenreSummary(id=str(genre.id), name=genre.content.canonical_name) for genre in genres],
        )
