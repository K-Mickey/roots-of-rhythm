from roots_of_rhythm.music_catalog.domain import (
    ClassificationAssignment,
    ClassificationContent,
    ClassificationTargetKind,
    EditorialStatus,
    EvidenceStatus,
    Genre,
    GeographicContext,
    HistoricalPeriod,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.music_catalog.infrastructure.models import (
    ClassificationAssignmentRecord,
    ClassificationConceptRecord,
)


def record_from_genre(genre: Genre) -> ClassificationConceptRecord:
    period = genre.content.period
    start = period.start if period is not None else None
    end = period.end if period is not None else None
    return ClassificationConceptRecord(
        id=genre.id,
        kind=genre.kind.value,
        editorial_status=genre.editorial_status.value,
        canonical_name=genre.content.canonical_name,
        aliases=list(genre.content.aliases),
        definition=genre.content.definition,
        boundaries=genre.content.boundaries,
        period_label=period.label if period is not None else None,
        period_start_year=start.year if start is not None else None,
        period_start_precision=start.precision.value if start is not None else None,
        period_end_year=end.year if end is not None else None,
        period_end_precision=end.precision.value if end is not None else None,
        geography_summary=genre.content.geography.summary if genre.content.geography is not None else None,
        historical_context=genre.content.historical_context,
        formation=genre.content.formation,
        characteristic_features=list(genre.content.characteristic_features),
        primary_image_id=genre.content.primary_image_id,
    )


def genre_from_record(record: ClassificationConceptRecord) -> Genre:
    start = _temporal_bound(record.period_start_year, record.period_start_precision)
    end = _temporal_bound(record.period_end_year, record.period_end_precision)
    period = (
        HistoricalPeriod(label=record.period_label, start=start, end=end) if record.period_label is not None else None
    )
    geography = GeographicContext(record.geography_summary) if record.geography_summary is not None else None
    content = ClassificationContent(
        canonical_name=record.canonical_name,
        aliases=tuple(record.aliases),
        definition=record.definition,
        boundaries=record.boundaries,
        period=period,
        geography=geography,
        historical_context=record.historical_context,
        formation=record.formation,
        characteristic_features=tuple(record.characteristic_features),
        primary_image_id=record.primary_image_id,
    )
    return Genre(id=record.id, content=content, editorial_status=EditorialStatus(record.editorial_status))


def update_record(record: ClassificationConceptRecord, genre: Genre) -> None:
    # Leave created_at / updated_at / deleted alone (DB trigger + soft-delete path).
    period = genre.content.period
    start = period.start if period is not None else None
    end = period.end if period is not None else None
    record.kind = genre.kind.value
    record.editorial_status = genre.editorial_status.value
    record.canonical_name = genre.content.canonical_name
    record.aliases = list(genre.content.aliases)
    record.definition = genre.content.definition
    record.boundaries = genre.content.boundaries
    record.period_label = period.label if period is not None else None
    record.period_start_year = start.year if start is not None else None
    record.period_start_precision = start.precision.value if start is not None else None
    record.period_end_year = end.year if end is not None else None
    record.period_end_precision = end.precision.value if end is not None else None
    record.geography_summary = genre.content.geography.summary if genre.content.geography is not None else None
    record.historical_context = genre.content.historical_context
    record.formation = genre.content.formation
    record.characteristic_features = list(genre.content.characteristic_features)
    record.primary_image_id = genre.content.primary_image_id


def record_from_assignment(assignment: ClassificationAssignment) -> ClassificationAssignmentRecord:
    return ClassificationAssignmentRecord(
        id=assignment.id,
        target_kind=assignment.target_kind.value,
        target_id=assignment.target_id,
        concept_id=assignment.concept_id,
        explanation=assignment.explanation,
        claim_id=assignment.claim_id,
        provenance=assignment.provenance,
        evidence_status=assignment.evidence_status.value,
        editorial_status=assignment.editorial_status.value,
    )


def assignment_from_record(record: ClassificationAssignmentRecord) -> ClassificationAssignment:
    return ClassificationAssignment(
        id=record.id,
        target_kind=ClassificationTargetKind(record.target_kind),
        target_id=record.target_id,
        concept_id=record.concept_id,
        explanation=record.explanation,
        claim_id=record.claim_id,
        provenance=record.provenance,
        evidence_status=EvidenceStatus(record.evidence_status),
        editorial_status=EditorialStatus(record.editorial_status),
    )


def update_assignment_record(record: ClassificationAssignmentRecord, assignment: ClassificationAssignment) -> None:
    record.target_kind = assignment.target_kind.value
    record.target_id = assignment.target_id
    record.concept_id = assignment.concept_id
    record.explanation = assignment.explanation
    record.claim_id = assignment.claim_id
    record.provenance = assignment.provenance
    record.evidence_status = assignment.evidence_status.value
    record.editorial_status = assignment.editorial_status.value


def _temporal_bound(year: int | None, precision: str | None) -> TemporalBound | None:
    if year is None or precision is None:
        return None
    return TemporalBound(year=year, precision=TemporalPrecision(precision))
