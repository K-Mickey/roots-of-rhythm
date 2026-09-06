from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import Genre


class FakeGenreRepository:
    def __init__(self, genres: dict[UUID, Genre]) -> None:
        self._genres = genres

    async def add(self, genre: Genre) -> None:
        self._genres[genre.id] = genre

    async def get(self, genre_id: UUID, *, for_update: bool = False) -> Genre | None:
        return self._genres.get(genre_id)

    async def get_by_ids(self, genre_ids: Collection[UUID], *, for_update: bool = False) -> dict[UUID, Genre]:
        return {genre_id: genre for genre_id in genre_ids if (genre := self._genres.get(genre_id)) is not None}

    async def get_published(self, genre_id: UUID, *, for_update: bool = False) -> Genre | None:
        genre = self._genres.get(genre_id)
        return genre if genre is not None and genre.is_published else None

    async def get_published_by_ids(self, genre_ids: Collection[UUID], *, for_update: bool = False) -> dict[UUID, Genre]:
        return {
            genre_id: genre
            for genre_id in genre_ids
            if (genre := self._genres.get(genre_id)) is not None and genre.is_published
        }

    async def list_published(self) -> list[Genre]:
        return sorted(
            (genre for genre in self._genres.values() if genre.is_published),
            key=lambda genre: genre.content.canonical_name,
        )

    async def save(self, genre: Genre) -> None:
        self._genres[genre.id] = genre

    async def mark_deleted(self, genre_id: UUID) -> None:
        self._genres.pop(genre_id, None)

    async def published_among(self, genre_ids: Collection[UUID]) -> set[UUID]:
        return {
            genre_id
            for genre_id in genre_ids
            if (genre := self._genres.get(genre_id)) is not None and genre.is_published
        }

    async def canonical_name_exists(self, canonical_name: str, *, excluding: UUID | None = None) -> bool:
        return any(
            genre.id != excluding and genre.content.canonical_name.lower() == canonical_name.lower()
            for genre in self._genres.values()
        )
