from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.historical_knowledge.application.errors import (
    ListeningGuideNotFound,
)
from roots_of_rhythm.historical_knowledge.application.ports import ListeningGuideRepository
from roots_of_rhythm.historical_knowledge.domain import ListeningGuide

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import ListeningObservation

type ListeningGuideRepositoryFactory = Callable[[Transaction], ListeningGuideRepository]


class ListeningGuideService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        guide_repository_factory: ListeningGuideRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._guide_repository_factory = guide_repository_factory

    async def create_draft(
        self,
        recording_id: UUID,
        observations: tuple[ListeningObservation, ...] = (),
        *,
        guide_id: UUID | None = None,
    ) -> ListeningGuide:
        guide = ListeningGuide.create_draft(recording_id, observations, guide_id=guide_id)
        async with self._transaction_scope() as transaction:
            await self._guide_repository_factory(transaction).add(guide)
            await transaction.commit()
        return guide

    async def archive(self, guide_id: UUID) -> ListeningGuide:
        async with self._transaction_scope() as transaction:
            guide_repository = self._guide_repository_factory(transaction)
            guide = await _get_guide(guide_repository, guide_id)
            archived = guide.archive()
            await guide_repository.save(archived)
            await transaction.commit()
        return archived


async def _get_guide(repository: ListeningGuideRepository, guide_id: UUID) -> ListeningGuide:
    guide = await repository.get(guide_id, for_update=True)
    if guide is None:
        raise ListeningGuideNotFound(str(guide_id))
    return guide
