from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.music_catalog.application.ports import GenreRepository

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import Genre

type GenreRepositoryFactory = Callable[[Transaction], GenreRepository]


class GenreReadService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        genre_repository_factory: GenreRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._genre_repository_factory = genre_repository_factory

    async def list_published(self) -> tuple[Genre, ...]:
        async with self._transaction_scope() as transaction:
            genres = await self._genre_repository_factory(transaction).list_published()
        return tuple(genres)

    async def get_published(self, genre_id: UUID) -> Genre | None:
        async with self._transaction_scope() as transaction:
            return await self._genre_repository_factory(transaction).get_published(genre_id)

    async def get_published_by_ids(self, genre_ids: Collection[UUID]) -> dict[UUID, Genre]:
        if not genre_ids:
            return {}
        async with self._transaction_scope() as transaction:
            return await self._genre_repository_factory(transaction).get_published_by_ids(genre_ids)
