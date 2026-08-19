from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from uuid import UUID, uuid7

from roots_of_rhythm.music_catalog.application.errors import (
    ClassificationAssignmentConflict,
    ClassificationAssignmentGenreNotPublished,
    ClassificationAssignmentNotFound,
    ClassificationAssignmentPersonNotPublished,
    ClassificationAssignmentTargetUnsupported,
    UniqueConstraintViolation,
)
from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
from roots_of_rhythm.music_catalog.domain import (
    ClassificationAssignment,
    ClassificationTargetKind,
    EvidenceStatus,
)
from roots_of_rhythm.people_catalog.application.ports import PeopleCatalogUnitOfWork

type MusicPeopleScopeFactory = Callable[
    [],
    AbstractAsyncContextManager[tuple[MusicCatalogUnitOfWork, PeopleCatalogUnitOfWork]],
]


class ClassificationAssignmentService:
    def __init__(self, catalogs: MusicPeopleScopeFactory) -> None:
        self._catalogs = catalogs

    async def create_for_person(
        self,
        person_id: UUID,
        concept_id: UUID,
        *,
        explanation: str | None = None,
        claim_id: UUID | None = None,
        provenance: str | None = None,
        evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED,
        assignment_id: UUID | None = None,
    ) -> ClassificationAssignment:
        async with self._catalogs() as (music, _people):
            assignment = ClassificationAssignment.create_for_person(
                assignment_id or uuid7(),
                person_id,
                concept_id=concept_id,
                explanation=explanation,
                claim_id=claim_id,
                provenance=provenance,
                evidence_status=evidence_status,
            )
            await music.assignments.add(assignment)
            await self._commit(music)
            return assignment

    async def replace_content(
        self,
        assignment_id: UUID,
        *,
        explanation: str | None,
        claim_id: UUID | None,
        provenance: str | None,
        evidence_status: EvidenceStatus,
    ) -> ClassificationAssignment:
        async with self._catalogs() as (music, _people):
            assignment = await music.assignments.get(assignment_id, for_update=True)
            if assignment is None:
                raise ClassificationAssignmentNotFound(str(assignment_id))
            updated = assignment.replace_content(
                explanation=explanation,
                claim_id=claim_id,
                provenance=provenance,
                evidence_status=evidence_status,
            )
            try:
                await music.assignments.save(updated)
            except LookupError as error:
                raise ClassificationAssignmentNotFound(str(assignment_id)) from error
            await self._commit(music)
            return updated

    async def publish(self, assignment_id: UUID) -> ClassificationAssignment:
        async with self._catalogs() as (music, people):
            assignment = await music.assignments.get(assignment_id, for_update=True)
            if assignment is None:
                raise ClassificationAssignmentNotFound(str(assignment_id))
            updated = assignment.publish()
            await self._ensure_target_published(assignment, people)
            if await music.genres.get_published(assignment.concept_id, for_update=True) is None:
                raise ClassificationAssignmentGenreNotPublished(str(assignment.concept_id))
            try:
                await music.assignments.save(updated)
            except LookupError as error:
                raise ClassificationAssignmentNotFound(str(assignment_id)) from error
            await self._commit(music)
            return updated

    @staticmethod
    async def _ensure_target_published(
        assignment: ClassificationAssignment,
        people: PeopleCatalogUnitOfWork,
    ) -> None:
        match assignment.target_kind:
            case ClassificationTargetKind.PERSON:
                if await people.persons.get_published(assignment.target_id, for_update=True) is None:
                    raise ClassificationAssignmentPersonNotPublished(str(assignment.target_id))
            case (
                ClassificationTargetKind.GROUP
                | ClassificationTargetKind.MUSICAL_WORK
                | ClassificationTargetKind.RECORDING
                | ClassificationTargetKind.RELEASE
            ):
                raise ClassificationAssignmentTargetUnsupported(assignment.target_kind.value)

    @staticmethod
    async def _commit(music: MusicCatalogUnitOfWork) -> None:
        try:
            await music.commit()
        except UniqueConstraintViolation as error:
            raise ClassificationAssignmentConflict from error
