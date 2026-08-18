from typing import TYPE_CHECKING, Self

from roots_of_rhythm.music_catalog.domain import EditorialStatus

if TYPE_CHECKING:
    from collections.abc import Collection
    from types import TracebackType
    from uuid import UUID

    from roots_of_rhythm.music_catalog.application.ports import GenreRepository
    from roots_of_rhythm.music_catalog.domain import Genre


class FakeGenreRepository:
    def __init__(self, genres: dict[UUID, Genre]) -> None:
        self._genres = genres

    async def add(self, genre: Genre) -> None:
        self._genres[genre.id] = genre

    async def get(self, genre_id: UUID) -> Genre | None:
        return self._genres.get(genre_id)

    async def get_published(self, genre_id: UUID) -> Genre | None:
        genre = self._genres.get(genre_id)
        return genre if genre is not None and genre.editorial_status is EditorialStatus.PUBLISHED else None

    async def save(self, genre: Genre) -> None:
        self._genres[genre.id] = genre

    async def mark_deleted(self, genre_id: UUID) -> None:
        self._genres.pop(genre_id, None)

    async def published_among(self, genre_ids: Collection[UUID]) -> set[UUID]:
        return {
            genre_id
            for genre_id in genre_ids
            if (genre := self._genres.get(genre_id)) is not None and genre.editorial_status is EditorialStatus.PUBLISHED
        }

    async def canonical_name_exists(self, canonical_name: str, *, excluding: UUID | None = None) -> bool:
        return any(
            genre.id != excluding and genre.content.canonical_name.lower() == canonical_name.lower()
            for genre in self._genres.values()
        )


class FakeMusicCatalogUnitOfWork:
    def __init__(self, genres: dict[UUID, Genre]) -> None:
        self.genres: GenreRepository = FakeGenreRepository(genres)
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
