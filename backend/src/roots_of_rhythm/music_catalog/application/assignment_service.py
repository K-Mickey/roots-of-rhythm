from collections.abc import Callable
from uuid import UUID, uuid7

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.music_catalog.application.errors import (
    ClassificationAssignmentConflict,
    ClassificationAssignmentNotFound,
    UniqueConstraintViolation,
)
from roots_of_rhythm.music_catalog.application.ports import ClassificationAssignmentRepository
from roots_of_rhythm.music_catalog.domain import ClassificationAssignment, EvidenceStatus

type ClassificationAssignmentRepositoryFactory = Callable[[Transaction], ClassificationAssignmentRepository]


class ClassificationAssignmentService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        assignment_repository_factory: ClassificationAssignmentRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._assignment_repository_factory = assignment_repository_factory

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
        assignment = ClassificationAssignment.create_for_person(
            assignment_id or uuid7(),
            person_id,
            concept_id=concept_id,
            explanation=explanation,
            claim_id=claim_id,
            provenance=provenance,
            evidence_status=evidence_status,
        )
        return await self._create(assignment)

    async def create_for_group(
        self,
        group_id: UUID,
        concept_id: UUID,
        *,
        explanation: str | None = None,
        claim_id: UUID | None = None,
        provenance: str | None = None,
        evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED,
        assignment_id: UUID | None = None,
    ) -> ClassificationAssignment:
        assignment = ClassificationAssignment.create_for_group(
            assignment_id or uuid7(),
            group_id,
            concept_id=concept_id,
            explanation=explanation,
            claim_id=claim_id,
            provenance=provenance,
            evidence_status=evidence_status,
        )
        return await self._create(assignment)

    async def replace_content(
        self,
        assignment_id: UUID,
        *,
        explanation: str | None,
        claim_id: UUID | None,
        provenance: str | None,
        evidence_status: EvidenceStatus,
    ) -> ClassificationAssignment:
        async with self._transaction_scope() as transaction:
            assignment_repository = self._assignment_repository_factory(transaction)
            assignment = await assignment_repository.get(assignment_id, for_update=True)
            if assignment is None:
                raise ClassificationAssignmentNotFound(str(assignment_id))
            updated = assignment.replace_content(
                explanation=explanation,
                claim_id=claim_id,
                provenance=provenance,
                evidence_status=evidence_status,
            )
            try:
                await assignment_repository.save(updated)
            except LookupError as error:
                raise ClassificationAssignmentNotFound(str(assignment_id)) from error
            except UniqueConstraintViolation as error:
                raise ClassificationAssignmentConflict from error
            await transaction.commit()
            return updated

    async def _create(self, assignment: ClassificationAssignment) -> ClassificationAssignment:
        async with self._transaction_scope() as transaction:
            assignment_repository = self._assignment_repository_factory(transaction)
            try:
                await assignment_repository.add(assignment)
            except UniqueConstraintViolation as error:
                raise ClassificationAssignmentConflict from error
            await transaction.commit()
            return assignment
