from asyncio import gather
from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.music_catalog.application.ports import (
    ClassificationAssignmentRepository,
    GenreRepository,
    GroupRepository,
    MusicalWorkRepository,
    RecordingRepository,
)
from roots_of_rhythm.music_catalog.public.recording_reader import (
    RecordingListData,
    RecordingOverviewData,
)

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import (
        ClassificationAssignment,
        Group,
        MusicalWork,
    )

type RecordingRepositoryFactory = Callable[[Transaction], RecordingRepository]
type AssignmentRepositoryFactory = Callable[[Transaction], ClassificationAssignmentRepository]
type WorkRepositoryFactory = Callable[[Transaction], MusicalWorkRepository]
type GenreRepositoryFactory = Callable[[Transaction], GenreRepository]
type GroupRepositoryFactory = Callable[[Transaction], GroupRepository]


class RecordingReadService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        recording_repository_factory: RecordingRepositoryFactory,
        assignment_repository_factory: AssignmentRepositoryFactory,
        work_repository_factory: WorkRepositoryFactory,
        genre_repository_factory: GenreRepositoryFactory,
        group_repository_factory: GroupRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._recording_repository_factory = recording_repository_factory
        self._assignment_repository_factory = assignment_repository_factory
        self._work_repository_factory = work_repository_factory
        self._genre_repository_factory = genre_repository_factory
        self._group_repository_factory = group_repository_factory

    async def list_overview(self) -> RecordingListData:
        async with self._transaction_scope() as transaction:
            recordings = await self._recording_repository_factory(transaction).list_published()
            if not recordings:
                return RecordingListData(
                    recordings=(),
                    assignments_by_recording={},
                    genres={},
                    groups={},
                    person_ids=frozenset(),
                )
            recording_ids = [recording.id for recording in recordings]
            person_ids = {
                credit.target_id
                for recording in recordings
                for credit in recording.credits
                if credit.is_primary_billing and credit.is_person_target
            }
            group_ids = {
                credit.target_id
                for recording in recordings
                for credit in recording.credits
                if credit.is_primary_billing and credit.is_group_target
            }

        assignments_by_recording, groups = await gather(
            self._load_assignments_for_recordings(recording_ids),
            self._load_groups_by_ids(group_ids),
        )
        genre_ids = {
            assignment.concept_id for assignments in assignments_by_recording.values() for assignment in assignments
        }
        async with self._transaction_scope() as transaction:
            genres = await self._genre_repository_factory(transaction).get_published_by_ids(genre_ids)

        return RecordingListData(
            recordings=tuple(recordings),
            assignments_by_recording=assignments_by_recording,
            genres=genres,
            groups=groups,
            person_ids=frozenset(person_ids),
        )

    async def get_recording_overview(self, recording_id: UUID) -> RecordingOverviewData:
        async with self._transaction_scope() as transaction:
            recording = await self._recording_repository_factory(transaction).get_published(recording_id)
            if recording is None:
                return RecordingOverviewData(
                    recording=None,
                    works={},
                    assignments=(),
                    genres={},
                    groups={},
                    person_ids=frozenset(),
                )
            work_ids = [usage.work_id for usage in recording.work_usages]
            person_ids = {credit.target_id for credit in recording.credits if credit.is_person_target}
            group_ids = {credit.target_id for credit in recording.credits if credit.is_group_target}

        works, assignments, groups = await gather(
            self._load_works_by_ids(work_ids),
            self._load_assignments_for_recording(recording_id),
            self._load_groups_by_ids(group_ids),
        )
        genre_ids = {assignment.concept_id for assignment in assignments}
        async with self._transaction_scope() as transaction:
            genres = await self._genre_repository_factory(transaction).get_published_by_ids(genre_ids)
        return RecordingOverviewData(
            recording=recording,
            works=works,
            assignments=assignments,
            genres=genres,
            groups=groups,
            person_ids=frozenset(person_ids),
        )

    async def _load_assignments_for_recordings(
        self,
        recording_ids: list[UUID],
    ) -> dict[UUID, tuple[ClassificationAssignment, ...]]:
        async with self._transaction_scope() as transaction:
            assignments_by_recording = await self._assignment_repository_factory(
                transaction
            ).list_published_for_recordings(recording_ids)
        return {recording_id: tuple(assignments) for recording_id, assignments in assignments_by_recording.items()}

    async def _load_assignments_for_recording(self, recording_id: UUID) -> tuple[ClassificationAssignment, ...]:
        async with self._transaction_scope() as transaction:
            assignments = await self._assignment_repository_factory(transaction).list_published_for_recording(
                recording_id
            )
        return tuple(assignments)

    async def _load_works_by_ids(self, work_ids: list[UUID]) -> dict[UUID, MusicalWork]:
        async with self._transaction_scope() as transaction:
            return await self._work_repository_factory(transaction).get_published_by_ids(work_ids)

    async def _load_groups_by_ids(self, group_ids: set[UUID]) -> dict[UUID, Group]:
        async with self._transaction_scope() as transaction:
            return await self._group_repository_factory(transaction).get_published_by_ids(group_ids)
