from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


class GenreUnitOfWorkStatusLookup:
    """Cross-context Genre status lookup with a session scoped to each operation."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def is_published(self, genre_id: UUID) -> bool:
        async with self._uow_factory() as uow:
            return await uow.genres.get_published(genre_id) is not None

    async def exists(self, genre_id: UUID) -> bool:
        async with self._uow_factory() as uow:
            return await uow.genres.get(genre_id) is not None

    async def published_among(self, genre_ids: Collection[UUID]) -> set[UUID]:
        async with self._uow_factory() as uow:
            return await uow.genres.published_among(genre_ids)
