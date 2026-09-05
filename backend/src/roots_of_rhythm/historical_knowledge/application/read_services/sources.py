from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.historical_knowledge.application.ports import SourceRepository

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import Source

type SourceRepositoryFactory = Callable[[Transaction], SourceRepository]


class SourceReadService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        source_repository_factory: SourceRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._source_repository_factory = source_repository_factory

    async def get_sources_by_ids(self, source_ids: Collection[UUID]) -> dict[UUID, Source]:
        if not source_ids:
            return {}
        ids = set(source_ids)
        async with self._transaction_scope() as transaction:
            return await self._source_repository_factory(transaction).get_sources_by_ids(ids)
