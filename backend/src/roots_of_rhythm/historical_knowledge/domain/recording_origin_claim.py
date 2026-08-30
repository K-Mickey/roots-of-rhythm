from typing import TYPE_CHECKING, Self
from uuid import UUID, uuid7

import msgspec

from roots_of_rhythm.historical_knowledge.domain.enums import (
    EditorialStatus,
    EvidenceRole,
    EvidenceStatus,
    RecordingOriginPredicate,
)
from roots_of_rhythm.historical_knowledge.domain.errors import ClaimPublicationError
from roots_of_rhythm.historical_knowledge.domain.value_objects import (
    ClaimEvidenceReference,
    ClaimProvenance,
    GeographicContext,
    HistoricalPeriod,
    _replacement,
    _required_text,
)
from roots_of_rhythm.text_lengths import TEXT_1024

if TYPE_CHECKING:
    from collections.abc import Sequence


class RecordingOriginClaim(msgspec.Struct, frozen=True):
    id: UUID
    recording_id: UUID
    work_id: UUID
    predicate: RecordingOriginPredicate
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
        recording_id: UUID,
        work_id: UUID,
        predicate: RecordingOriginPredicate,
        *,
        claim_id: UUID | None = None,
    ) -> Self:
        return cls(
            id=claim_id or uuid7(),
            recording_id=recording_id,
            work_id=work_id,
            predicate=predicate,
        )

    def replace_content(
        self,
        *,
        explanation: str | None = None,
        temporal: HistoricalPeriod | None = None,
        geographic: GeographicContext | None = None,
        provenance: ClaimProvenance | None = None,
        evidence_status: EvidenceStatus | None = None,
        clear_explanation: bool = False,
        clear_temporal: bool = False,
        clear_geographic: bool = False,
        clear_provenance: bool = False,
    ) -> "RecordingOriginClaim":
        next_explanation = _replacement(self.explanation, explanation, clear=clear_explanation)
        if next_explanation is not None:
            next_explanation = _required_text(next_explanation, "explanation", max_length=TEXT_1024)
        next_temporal = _replacement(self.temporal, temporal, clear=clear_temporal)
        next_geographic = _replacement(self.geographic, geographic, clear=clear_geographic)
        next_provenance = _replacement(self.provenance, provenance, clear=clear_provenance)
        next_evidence_status = self.evidence_status if evidence_status is None else evidence_status
        updated = RecordingOriginClaim(
            id=self.id,
            recording_id=self.recording_id,
            work_id=self.work_id,
            predicate=self.predicate,
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

    def replace_evidence(self, references: tuple[ClaimEvidenceReference, ...]) -> "RecordingOriginClaim":
        updated = RecordingOriginClaim(
            id=self.id,
            recording_id=self.recording_id,
            work_id=self.work_id,
            predicate=self.predicate,
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

    def submit_for_review(self) -> "RecordingOriginClaim":
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> "RecordingOriginClaim":
        self._publication_missing_fields()
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "RecordingOriginClaim":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "RecordingOriginClaim":
        return RecordingOriginClaim(
            id=self.id,
            recording_id=self.recording_id,
            work_id=self.work_id,
            predicate=self.predicate,
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


def is_recording_origin_badge_visible(
    claim: RecordingOriginClaim,
    *,
    recording_published: bool,
    work_published: bool,
) -> bool:
    return (
        claim.editorial_status is EditorialStatus.PUBLISHED
        and claim.evidence_status is EvidenceStatus.SUPPORTED
        and recording_published
        and work_published
    )


def origin_badge_values(claims: Sequence[RecordingOriginClaim]) -> list[str]:
    present = {claim.predicate for claim in claims}
    return [predicate.value for predicate in RecordingOriginPredicate if predicate in present]
