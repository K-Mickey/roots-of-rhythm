from uuid import UUID

import msgspec

from roots_of_rhythm.music_catalog.domain.enums import ClassificationTargetKind, EditorialStatus, EvidenceStatus
from roots_of_rhythm.music_catalog.domain.errors import ClassificationAssignmentPublicationError
from roots_of_rhythm.music_catalog.domain.value_objects import LONG_TEXT_MAX_LENGTH, optional_text


class ClassificationAssignment(msgspec.Struct, frozen=True):
    id: UUID
    target_kind: ClassificationTargetKind
    target_id: UUID
    concept_id: UUID
    explanation: str | None = None
    claim_id: UUID | None = None
    provenance: str | None = None
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED
    editorial_status: EditorialStatus = EditorialStatus.DRAFT

    @classmethod
    def create_for_person(
        cls,
        assignment_id: UUID,
        person_id: UUID,
        concept_id: UUID,
        *,
        explanation: str | None = None,
        claim_id: UUID | None = None,
        provenance: str | None = None,
        evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED,
    ) -> "ClassificationAssignment":
        return cls(
            id=assignment_id,
            target_kind=ClassificationTargetKind.PERSON,
            target_id=person_id,
            concept_id=concept_id,
            explanation=optional_text(explanation, "explanation", max_length=LONG_TEXT_MAX_LENGTH),
            claim_id=claim_id,
            provenance=optional_text(provenance, "provenance", max_length=LONG_TEXT_MAX_LENGTH),
            evidence_status=evidence_status,
        )

    def replace_content(
        self,
        *,
        explanation: str | None,
        claim_id: UUID | None,
        provenance: str | None,
        evidence_status: EvidenceStatus,
    ) -> "ClassificationAssignment":
        return ClassificationAssignment(
            id=self.id,
            target_kind=self.target_kind,
            target_id=self.target_id,
            concept_id=self.concept_id,
            explanation=optional_text(explanation, "explanation", max_length=LONG_TEXT_MAX_LENGTH),
            claim_id=claim_id,
            provenance=optional_text(provenance, "provenance", max_length=LONG_TEXT_MAX_LENGTH),
            evidence_status=evidence_status,
            editorial_status=self.editorial_status,
        )

    def publish(self) -> "ClassificationAssignment":
        invalid: list[str] = []
        if self.explanation is None and self.claim_id is None:
            invalid.append("explanation_or_claim_id")
        if self.provenance is None:
            invalid.append("provenance")
        if self.evidence_status is not EvidenceStatus.UNVERIFIED:
            invalid.append("evidence_status")
        if invalid:
            raise ClassificationAssignmentPublicationError(tuple(invalid))
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "ClassificationAssignment":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "ClassificationAssignment":
        return ClassificationAssignment(
            id=self.id,
            target_kind=self.target_kind,
            target_id=self.target_id,
            concept_id=self.concept_id,
            explanation=self.explanation,
            claim_id=self.claim_id,
            provenance=self.provenance,
            evidence_status=self.evidence_status,
            editorial_status=status,
        )
