from typing import Self
from uuid import UUID, uuid7

import msgspec

from roots_of_rhythm.historical_knowledge.domain.enums import (
    EditorialStatus,
    EvidenceRole,
    EvidenceStatus,
    RelationType,
)
from roots_of_rhythm.historical_knowledge.domain.errors import ClaimPublicationError
from roots_of_rhythm.historical_knowledge.domain.value_objects import (
    LONG_TEXT_MAX_LENGTH,
    ClaimEvidenceReference,
    ClaimProvenance,
    GeographicContext,
    HistoricalPeriod,
    _required_text,
    canonicalize_relation_endpoints,
)


class GenreRelationClaim(msgspec.Struct, frozen=True):
    id: UUID
    subject_genre_id: UUID
    target_genre_id: UUID
    relation_type: RelationType
    editorial_status: EditorialStatus = EditorialStatus.DRAFT
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED
    explanation: str | None = None
    temporal: HistoricalPeriod | None = None
    geographic: GeographicContext | None = None
    provenance: ClaimProvenance | None = None
    evidence_references: tuple[ClaimEvidenceReference, ...] = ()

    @classmethod
    def create_draft(
        cls,
        subject_genre_id: UUID,
        target_genre_id: UUID,
        relation_type: RelationType,
        *,
        claim_id: UUID | None = None,
    ) -> Self:
        subject, target = canonicalize_relation_endpoints(subject_genre_id, target_genre_id, relation_type)
        return cls(
            id=claim_id or uuid7(),
            subject_genre_id=subject,
            target_genre_id=target,
            relation_type=relation_type,
        )

    def replace_content(
        self,
        *,
        relation_type: RelationType | None = None,
        explanation: str | None = None,
        temporal: HistoricalPeriod | None = None,
        geographic: GeographicContext | None = None,
        provenance: ClaimProvenance | None = None,
        evidence_status: EvidenceStatus | None = None,
        clear_explanation: bool = False,
        clear_temporal: bool = False,
        clear_geographic: bool = False,
        clear_provenance: bool = False,
    ) -> "GenreRelationClaim":
        next_type = self.relation_type if relation_type is None else relation_type
        subject, target = canonicalize_relation_endpoints(self.subject_genre_id, self.target_genre_id, next_type)
        next_explanation = None if clear_explanation else (self.explanation if explanation is None else explanation)
        if next_explanation is not None:
            next_explanation = _required_text(next_explanation, "explanation", max_length=LONG_TEXT_MAX_LENGTH)
        next_temporal = None if clear_temporal else (self.temporal if temporal is None else temporal)
        next_geographic = None if clear_geographic else (self.geographic if geographic is None else geographic)
        next_provenance = None if clear_provenance else (self.provenance if provenance is None else provenance)
        next_evidence_status = self.evidence_status if evidence_status is None else evidence_status
        updated = GenreRelationClaim(
            id=self.id,
            subject_genre_id=subject,
            target_genre_id=target,
            relation_type=next_type,
            editorial_status=self.editorial_status,
            evidence_status=next_evidence_status,
            explanation=next_explanation,
            temporal=next_temporal,
            geographic=next_geographic,
            provenance=next_provenance,
            evidence_references=self.evidence_references,
        )
        if self.editorial_status is EditorialStatus.PUBLISHED:
            updated._publication_missing_fields()
        return updated

    def replace_evidence(self, references: tuple[ClaimEvidenceReference, ...]) -> "GenreRelationClaim":
        updated = GenreRelationClaim(
            id=self.id,
            subject_genre_id=self.subject_genre_id,
            target_genre_id=self.target_genre_id,
            relation_type=self.relation_type,
            editorial_status=self.editorial_status,
            evidence_status=self.evidence_status,
            explanation=self.explanation,
            temporal=self.temporal,
            geographic=self.geographic,
            provenance=self.provenance,
            evidence_references=references,
        )
        if self.editorial_status is EditorialStatus.PUBLISHED:
            updated._publication_missing_fields()
        return updated

    def submit_for_review(self) -> "GenreRelationClaim":
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> "GenreRelationClaim":
        self._publication_missing_fields()
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "GenreRelationClaim":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "GenreRelationClaim":
        return GenreRelationClaim(
            id=self.id,
            subject_genre_id=self.subject_genre_id,
            target_genre_id=self.target_genre_id,
            relation_type=self.relation_type,
            editorial_status=status,
            evidence_status=self.evidence_status,
            explanation=self.explanation,
            temporal=self.temporal,
            geographic=self.geographic,
            provenance=self.provenance,
            evidence_references=self.evidence_references,
        )

    def _publication_missing_fields(self) -> None:
        missing: list[str] = []
        if self.explanation is None:
            missing.append("explanation")
        if self.temporal is None:
            missing.append("temporal")
        if self.geographic is None:
            missing.append("geographic")
        if self.provenance is None:
            missing.append("provenance")
        if self.evidence_status is EvidenceStatus.SUPPORTED and not any(
            reference.role is EvidenceRole.SUPPORTS for reference in self.evidence_references
        ):
            missing.append("supported_evidence")
        if self.evidence_status is EvidenceStatus.DISPUTED and not any(
            reference.role is EvidenceRole.OPPOSES for reference in self.evidence_references
        ):
            missing.append("opposing_evidence")
        if missing:
            raise ClaimPublicationError(tuple(missing))


def is_claim_publicly_visible(
    claim: GenreRelationClaim,
    *,
    subject_published: bool,
    target_published: bool,
) -> bool:
    return claim.editorial_status is EditorialStatus.PUBLISHED and subject_published and target_published
