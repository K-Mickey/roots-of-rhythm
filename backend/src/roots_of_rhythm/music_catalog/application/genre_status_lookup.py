from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.music_catalog.application.ports import GenreRepository


class GenreRepositoryStatusLookup:
    """Cross-context read adapter: Genre status without exposing the full GenreRepository."""

    def __init__(self, genres: GenreRepository) -> None:
        self._genres = genres

    async def is_published(self, genre_id: UUID) -> bool:
        return await self._genres.get_published(genre_id) is not None

    async def exists(self, genre_id: UUID) -> bool:
        return await self._genres.get(genre_id) is not None

    async def published_among(self, genre_ids: Collection[UUID]) -> set[UUID]:
        return await self._genres.published_among(genre_ids)
