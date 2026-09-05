from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.music_catalog.application.ports import MusicalWorkRepository

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.domain import MusicalWork

type WorkRepositoryFactory = Callable[[Transaction], MusicalWorkRepository]


class SongListReadService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        work_repository_factory: WorkRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._work_repository_factory = work_repository_factory

    async def list_published_works(self) -> tuple[MusicalWork, ...]:
        async with self._transaction_scope() as transaction:
            works = await self._work_repository_factory(transaction).list_published()
        return tuple(works)
