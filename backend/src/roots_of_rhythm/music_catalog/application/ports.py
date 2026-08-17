from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from types import TracebackType
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import Genre


class GenreRepository(Protocol):
    async def add(self, genre: Genre) -> None: ...

    async def get(self, genre_id: UUID) -> Genre | None: ...

    async def get_published(self, genre_id: UUID) -> Genre | None: ...

    async def save(self, genre: Genre) -> None: ...

    async def canonical_name_exists(self, canonical_name: str, *, excluding: UUID | None = None) -> bool: ...


class MusicCatalogUnitOfWork(Protocol):
    genres: GenreRepository

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
