from collections.abc import Awaitable, Callable
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

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]
type PersonPublishedLookup = Callable[[UUID], Awaitable[bool]]


class ClassificationAssignmentService:
    def __init__(self, uow_factory: UnitOfWorkFactory, person_published: PersonPublishedLookup) -> None:
        self._uow_factory = uow_factory
        self._person_published = person_published

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
        async with self._uow_factory() as uow:
            assignment = ClassificationAssignment.create_for_person(
                assignment_id or uuid7(),
                person_id,
                concept_id=concept_id,
                explanation=explanation,
                claim_id=claim_id,
                provenance=provenance,
                evidence_status=evidence_status,
            )
            await uow.assignments.add(assignment)
            await self._commit(uow)
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
        async with self._uow_factory() as uow:
            assignment = await uow.assignments.get(assignment_id)
            if assignment is None:
                raise ClassificationAssignmentNotFound(str(assignment_id))
            updated = assignment.replace_content(
                explanation=explanation,
                claim_id=claim_id,
                provenance=provenance,
                evidence_status=evidence_status,
            )
            try:
                await uow.assignments.save(updated)
            except LookupError as error:
                raise ClassificationAssignmentNotFound(str(assignment_id)) from error
            await self._commit(uow)
            return updated

    async def publish(self, assignment_id: UUID) -> ClassificationAssignment:
        async with self._uow_factory() as uow:
            assignment = await uow.assignments.get(assignment_id)
            if assignment is None:
                raise ClassificationAssignmentNotFound(str(assignment_id))
            updated = assignment.publish()
            await self._ensure_target_published(assignment)
            if await uow.genres.get_published(assignment.concept_id) is None:
                raise ClassificationAssignmentGenreNotPublished(str(assignment.concept_id))
            try:
                await uow.assignments.save(updated)
            except LookupError as error:
                raise ClassificationAssignmentNotFound(str(assignment_id)) from error
            await self._commit(uow)
            return updated

    async def _ensure_target_published(self, assignment: ClassificationAssignment) -> None:
        match assignment.target_kind:
            case ClassificationTargetKind.PERSON:
                if not await self._person_published(assignment.target_id):
                    raise ClassificationAssignmentPersonNotPublished(str(assignment.target_id))
            case (
                ClassificationTargetKind.GROUP
                | ClassificationTargetKind.MUSICAL_WORK
                | ClassificationTargetKind.RECORDING
                | ClassificationTargetKind.RELEASE
            ):
                raise ClassificationAssignmentTargetUnsupported(assignment.target_kind.value)

    @staticmethod
    async def _commit(uow: MusicCatalogUnitOfWork) -> None:
        try:
            await uow.commit()
        except UniqueConstraintViolation as error:
            raise ClassificationAssignmentConflict from error
