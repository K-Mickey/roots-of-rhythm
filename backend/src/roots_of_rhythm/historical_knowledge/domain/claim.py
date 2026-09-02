from typing import Self
from uuid import UUID, uuid7

import msgspec

from roots_of_rhythm.historical_knowledge.domain.enums import (
    EditorialStatus,
    EvidenceStatus,
    RelationType,
)
from roots_of_rhythm.historical_knowledge.domain.errors import ClaimPublicationError
from roots_of_rhythm.historical_knowledge.domain.value_objects import (
    ClaimEvidenceReference,
    ClaimProvenance,
    GeographicContext,
    HistoricalPeriod,
    _replacement,
    _required_text,
    canonicalize_relation_endpoints,
)
from roots_of_rhythm.text_lengths import TEXT_1024


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

    @property
    def is_published(self) -> bool:
        return self.editorial_status is EditorialStatus.PUBLISHED

    @property
    def is_draft(self) -> bool:
        return self.editorial_status is EditorialStatus.DRAFT

    @property
    def is_unverified(self) -> bool:
        return self.evidence_status is EvidenceStatus.UNVERIFIED

    @property
    def is_disputed(self) -> bool:
        return self.evidence_status is EvidenceStatus.DISPUTED

    @property
    def is_supported(self) -> bool:
        return self.evidence_status is EvidenceStatus.SUPPORTED

    @property
    def is_overlaps_with(self) -> bool:
        return self.relation_type is RelationType.OVERLAPS_WITH

    @property
    def is_developed_from(self) -> bool:
        return self.relation_type is RelationType.DEVELOPED_FROM

    @property
    def is_contributed_to_emergence_of(self) -> bool:
        return self.relation_type is RelationType.CONTRIBUTED_TO_EMERGENCE_OF

    def get_verified_evidence_references(self) -> tuple[ClaimEvidenceReference, ...]:
        if self.is_supported:
            return tuple(reference for reference in self.evidence_references if reference.is_supports)
        if self.is_disputed:
            return tuple(reference for reference in self.evidence_references if reference.is_opposes)
        return ()

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
        next_explanation = _replacement(self.explanation, explanation, clear=clear_explanation)
        if next_explanation is not None:
            next_explanation = _required_text(next_explanation, "explanation", max_length=TEXT_1024)
        next_temporal = _replacement(self.temporal, temporal, clear=clear_temporal)
        next_geographic = _replacement(self.geographic, geographic, clear=clear_geographic)
        next_provenance = _replacement(self.provenance, provenance, clear=clear_provenance)
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
        if self.is_published:
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
        if self.is_published:
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
        if self.is_supported and not any(reference.is_supports for reference in self.evidence_references):
            missing.append("supported_evidence")
        if self.is_disputed and not any(reference.is_opposes for reference in self.evidence_references):
            missing.append("opposing_evidence")
        if missing:
            raise ClaimPublicationError(tuple(missing))


def is_claim_publicly_visible(
    claim: GenreRelationClaim,
    *,
    subject_published: bool,
    target_published: bool,
) -> bool:
    return claim.is_published and subject_published and target_published
