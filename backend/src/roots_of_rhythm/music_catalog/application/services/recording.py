from collections.abc import Callable
from uuid import UUID, uuid7

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.music_catalog.application.errors import (
    RecordingConflict,
    RecordingNotFound,
    UniqueConstraintViolation,
)
from roots_of_rhythm.music_catalog.application.ports import RecordingRepository
from roots_of_rhythm.music_catalog.domain import Recording, RecordingContent

type RecordingRepositoryFactory = Callable[[Transaction], RecordingRepository]


class RecordingService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        recording_repository_factory: RecordingRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._recording_repository_factory = recording_repository_factory

    async def create(self, content: RecordingContent, *, recording_id: UUID | None = None) -> Recording:
        async with self._transaction_scope() as transaction:
            recording = Recording.create(recording_id or uuid7(), content)
            repository = self._recording_repository_factory(transaction)
            try:
                await repository.add(recording)
            except UniqueConstraintViolation as error:
                raise RecordingConflict from error
            await transaction.commit()
            return recording

    async def archive(self, recording_id: UUID) -> Recording:
        async with self._transaction_scope() as transaction:
            recording_repository = self._recording_repository_factory(transaction)

            recording = await recording_repository.get(recording_id, for_update=True)
            if recording is None:
                raise RecordingNotFound(str(recording_id))

            updated = recording.archive()
            try:
                await recording_repository.save_status(updated)
            except LookupError as error:
                raise RecordingNotFound(str(updated.id)) from error

            await transaction.commit()
            return updated
