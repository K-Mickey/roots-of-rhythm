from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.music_catalog.application.errors import (
    ClassificationAssignmentConflict,
    ClassificationAssignmentGenreNotPublished,
    ClassificationAssignmentGroupNotPublished,
    ClassificationAssignmentNotFound,
    ClassificationAssignmentPersonNotPublished,
    ClassificationAssignmentTargetUnsupported,
    UniqueConstraintViolation,
)
from roots_of_rhythm.music_catalog.application.ports import (
    ClassificationAssignmentRepository,
    GenreRepository,
    GroupRepository,
)
from roots_of_rhythm.music_catalog.domain import ClassificationAssignment, ClassificationTargetKind
from roots_of_rhythm.people_catalog.application.ports import PersonRepository

if TYPE_CHECKING:
    from uuid import UUID

type ClassificationAssignmentRepositoryFactory = Callable[[Transaction], ClassificationAssignmentRepository]
type GenreRepositoryFactory = Callable[[Transaction], GenreRepository]
type GroupRepositoryFactory = Callable[[Transaction], GroupRepository]
type PersonRepositoryFactory = Callable[[Transaction], PersonRepository]


class PublishClassificationAssignment:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        assignment_repository_factory: ClassificationAssignmentRepositoryFactory,
        genre_repository_factory: GenreRepositoryFactory,
        group_repository_factory: GroupRepositoryFactory,
        person_repository_factory: PersonRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._assignment_repository_factory = assignment_repository_factory
        self._genre_repository_factory = genre_repository_factory
        self._group_repository_factory = group_repository_factory
        self._person_repository_factory = person_repository_factory

    async def execute(self, assignment_id: UUID) -> ClassificationAssignment:
        async with self._transaction_scope() as transaction:
            assignment_repository = self._assignment_repository_factory(transaction)
            assignment = await assignment_repository.get(assignment_id, for_update=True)
            if assignment is None:
                raise ClassificationAssignmentNotFound(str(assignment_id))

            published = assignment.publish()
            await self._ensure_genre_and_target_published(transaction, assignment)
            try:
                await assignment_repository.save(published)
            except LookupError as error:
                raise ClassificationAssignmentNotFound(str(assignment_id)) from error
            except UniqueConstraintViolation as error:
                raise ClassificationAssignmentConflict from error
            await transaction.commit()
            return published

    async def _ensure_genre_and_target_published(
        self,
        transaction: Transaction,
        assignment: ClassificationAssignment,
    ) -> None:
        genre_repository = self._genre_repository_factory(transaction)
        if await genre_repository.get_published(assignment.concept_id, for_update=True) is None:
            raise ClassificationAssignmentGenreNotPublished(str(assignment.concept_id))

        match assignment.target_kind:
            case ClassificationTargetKind.PERSON:
                person_repository = self._person_repository_factory(transaction)
                if await person_repository.get_published(assignment.target_id, for_update=True) is None:
                    raise ClassificationAssignmentPersonNotPublished(str(assignment.target_id))
            case ClassificationTargetKind.GROUP:
                group_repository = self._group_repository_factory(transaction)
                if await group_repository.get_published(assignment.target_id, for_update=True) is None:
                    raise ClassificationAssignmentGroupNotPublished(str(assignment.target_id))
            case (
                ClassificationTargetKind.MUSICAL_WORK
                | ClassificationTargetKind.RECORDING
                | ClassificationTargetKind.RELEASE
            ):
                raise ClassificationAssignmentTargetUnsupported(assignment.target_kind.value)
