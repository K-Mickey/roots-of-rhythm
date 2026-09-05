from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.historical_knowledge.application.errors import (
    ListeningGuideNotFound,
    ListeningGuideRecordingNotPublished,
)
from roots_of_rhythm.historical_knowledge.application.ports import ListeningGuideRepository
from roots_of_rhythm.music_catalog.application.ports import RecordingRepository

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import ListeningGuide, ListeningObservation

type ListeningGuideRepositoryFactory = Callable[[Transaction], ListeningGuideRepository]
type RecordingRepositoryFactory = Callable[[Transaction], RecordingRepository]


class ReplaceListeningGuideObservations:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        guide_repository_factory: ListeningGuideRepositoryFactory,
        recording_repository_factory: RecordingRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._guide_repository_factory = guide_repository_factory
        self._recording_repository_factory = recording_repository_factory

    async def execute(
        self,
        guide_id: UUID,
        observations: tuple[ListeningObservation, ...],
    ) -> ListeningGuide:
        async with self._transaction_scope() as transaction:
            guide_repository = self._guide_repository_factory(transaction)
            guide = await guide_repository.get(guide_id, for_update=True)
            if guide is None:
                raise ListeningGuideNotFound(str(guide_id))
            updated = guide.replace_observations(observations)
            if updated.is_published and (
                await self._recording_repository_factory(transaction).get_published(
                    guide.recording_id,
                    for_update=True,
                )
                is None
            ):
                raise ListeningGuideRecordingNotPublished(str(guide.recording_id))
            await guide_repository.save(updated)
            await transaction.commit()
            return updated


class PublishListeningGuide:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        guide_repository_factory: ListeningGuideRepositoryFactory,
        recording_repository_factory: RecordingRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._guide_repository_factory = guide_repository_factory
        self._recording_repository_factory = recording_repository_factory

    async def execute(self, guide_id: UUID) -> ListeningGuide:
        async with self._transaction_scope() as transaction:
            guide_repository = self._guide_repository_factory(transaction)
            guide = await guide_repository.get(guide_id, for_update=True)
            if guide is None:
                raise ListeningGuideNotFound(str(guide_id))
            if (
                await self._recording_repository_factory(transaction).get_published(
                    guide.recording_id,
                    for_update=True,
                )
                is None
            ):
                raise ListeningGuideRecordingNotPublished(str(guide.recording_id))
            published = guide.publish()
            await guide_repository.save(published)
            await transaction.commit()
            return published
