from uuid import UUID, uuid7

from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EditorialStatus,
    EvidenceStatus,
    GenreRelationClaim,
    GeographicContext,
    HistoricalPeriod,
    RelationType,
)
from roots_of_rhythm.music_catalog.domain import ClassificationContent, Genre
from roots_of_rhythm.music_catalog.domain import EditorialStatus as GenreEditorialStatus


def published_genre(name: str, genre_id: UUID | None = None) -> Genre:
    return Genre(
        id=genre_id or uuid7(),
        content=ClassificationContent.create(name, definition=f"{name} definition"),
        editorial_status=GenreEditorialStatus.PUBLISHED,
    )


def published_relation_claim(
    *,
    subject: UUID,
    target: UUID,
    relation_type: RelationType,
    explanation: str,
    temporal: HistoricalPeriod | None,
    evidence_status: EvidenceStatus = EvidenceStatus.SUPPORTED,
    evidence: tuple[ClaimEvidenceReference, ...] = (),
    claim_id: UUID | None = None,
) -> GenreRelationClaim:
    return GenreRelationClaim(
        id=claim_id or uuid7(),
        subject_genre_id=subject,
        target_genre_id=target,
        relation_type=relation_type,
        editorial_status=EditorialStatus.PUBLISHED,
        evidence_status=evidence_status,
        explanation=explanation,
        temporal=temporal,
        geographic=GeographicContext.create("United States"),
        provenance=ClaimProvenance.create("research"),
        evidence_references=evidence,
    )
