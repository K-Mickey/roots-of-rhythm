from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.music_catalog.application.ports import (
    ClassificationAssignmentRepository,
    GenreRepository,
)
from roots_of_rhythm.music_catalog.public.performer_reader import PerformerData

if TYPE_CHECKING:
    from uuid import UUID

type AssignmentRepositoryFactory = Callable[[Transaction], ClassificationAssignmentRepository]
type GenreRepositoryFactory = Callable[[Transaction], GenreRepository]


class PerformerReadService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        assignment_repository_factory: AssignmentRepositoryFactory,
        genre_repository_factory: GenreRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._assignment_repository_factory = assignment_repository_factory
        self._genre_repository_factory = genre_repository_factory

    async def get_performer_data(self, person_id: UUID) -> PerformerData:
        async with self._transaction_scope() as transaction:
            assignments = await self._assignment_repository_factory(transaction).list_published_for_person(person_id)
            genre_ids = {assignment.concept_id for assignment in assignments}
            genres = await self._genre_repository_factory(transaction).get_published_by_ids(genre_ids)
        return PerformerData(assignments=tuple(assignments), genres=genres)
