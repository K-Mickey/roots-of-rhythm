from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import Genre


class GenreReader(Protocol):
    async def list_published(self) -> tuple[Genre, ...]: ...

    async def get_published(self, genre_id: UUID) -> Genre | None: ...

    async def get_published_by_ids(self, genre_ids: Collection[UUID]) -> dict[UUID, Genre]: ...
