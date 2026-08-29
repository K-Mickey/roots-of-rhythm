from uuid import uuid7

from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EditorialStatus,
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    GenreRelationClaim,
    GeographicContext,
    HistoricalPeriod,
    RecordingOriginClaim,
    RecordingOriginPredicate,
    RelationType,
    Source,
    SourceAccessPolicy,
    SourceFragment,
    SourceVersion,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    ClaimEvidenceReferenceRecord,
    GenreRelationClaimRecord,
    RecordingOriginClaimEvidenceReferenceRecord,
    RecordingOriginClaimRecord,
    SourceFragmentRecord,
    SourceRecord,
    SourceVersionRecord,
)


def source_from_record(record: SourceRecord) -> Source:
    return Source(
        id=record.id,
        title=record.title,
        author=record.author,
        responsible_organization=record.responsible_organization,
        publication=record.publication,
        publication_date=record.publication_date,
        external_url=record.external_url,
        access_policy=SourceAccessPolicy(record.access_policy),
    )


def record_from_source(source: Source) -> SourceRecord:
    return SourceRecord(
        id=source.id,
        title=source.title,
        author=source.author,
        responsible_organization=source.responsible_organization,
        publication=source.publication,
        publication_date=source.publication_date,
        external_url=source.external_url,
        access_policy=source.access_policy.value,
    )


def version_from_record(record: SourceVersionRecord) -> SourceVersion:
    return SourceVersion(id=record.id, source_id=record.source_id, label=record.label)


def record_from_version(version: SourceVersion) -> SourceVersionRecord:
    return SourceVersionRecord(id=version.id, source_id=version.source_id, label=version.label)


def fragment_from_record(record: SourceFragmentRecord) -> SourceFragment:
    return SourceFragment(
        id=record.id,
        source_version_id=record.source_version_id,
        review_status=FragmentReviewStatus(record.review_status),
        locator_text=record.locator_text,
        external_url=record.external_url,
    )


def record_from_fragment(fragment: SourceFragment) -> SourceFragmentRecord:
    return SourceFragmentRecord(
        id=fragment.id,
        source_version_id=fragment.source_version_id,
        review_status=fragment.review_status.value,
        locator_text=fragment.locator_text,
        external_url=fragment.external_url,
    )


def update_fragment_record(record: SourceFragmentRecord, fragment: SourceFragment) -> None:
    # Leave created_at / updated_at / deleted alone (DB trigger + soft-delete path).
    record.review_status = fragment.review_status.value
    record.locator_text = fragment.locator_text
    record.external_url = fragment.external_url


def claim_from_records(
    record: GenreRelationClaimRecord,
    evidence_records: list[ClaimEvidenceReferenceRecord],
) -> GenreRelationClaim:
    return GenreRelationClaim(
        id=record.id,
        subject_genre_id=record.subject_genre_id,
        target_genre_id=record.target_genre_id,
        relation_type=RelationType(record.relation_type),
        editorial_status=EditorialStatus(record.editorial_status),
        evidence_status=EvidenceStatus(record.evidence_status),
        explanation=record.explanation,
        temporal=_temporal(record),
        geographic=GeographicContext(record.geography_summary) if record.geography_summary is not None else None,
        provenance=ClaimProvenance(record.provenance_summary) if record.provenance_summary is not None else None,
        evidence_references=tuple(
            ClaimEvidenceReference(
                source_fragment_id=item.source_fragment_id,
                role=EvidenceRole(item.role),
                locator_text=item.locator_text,
                external_url=item.external_url,
            )
            for item in evidence_records
        ),
    )


def record_from_claim(claim: GenreRelationClaim) -> GenreRelationClaimRecord:
    period = claim.temporal
    start = period.start if period is not None else None
    end = period.end if period is not None else None
    return GenreRelationClaimRecord(
        id=claim.id,
        subject_genre_id=claim.subject_genre_id,
        target_genre_id=claim.target_genre_id,
        relation_type=claim.relation_type.value,
        editorial_status=claim.editorial_status.value,
        evidence_status=claim.evidence_status.value,
        explanation=claim.explanation,
        period_label=period.label if period is not None else None,
        period_start_year=start.year if start is not None else None,
        period_start_precision=start.precision.value if start is not None else None,
        period_end_year=end.year if end is not None else None,
        period_end_precision=end.precision.value if end is not None else None,
        geography_summary=claim.geographic.summary if claim.geographic is not None else None,
        provenance_summary=claim.provenance.summary if claim.provenance is not None else None,
    )


def evidence_records_from_claim(claim: GenreRelationClaim) -> list[ClaimEvidenceReferenceRecord]:
    return [
        ClaimEvidenceReferenceRecord(
            id=uuid7(),
            claim_id=claim.id,
            source_fragment_id=reference.source_fragment_id,
            role=reference.role.value,
            locator_text=reference.locator_text,
            external_url=reference.external_url,
        )
        for reference in claim.evidence_references
    ]


def update_claim_record(record: GenreRelationClaimRecord, claim: GenreRelationClaim) -> None:
    # Leave created_at / updated_at / deleted alone (DB trigger + soft-delete path).
    period = claim.temporal
    start = period.start if period is not None else None
    end = period.end if period is not None else None
    record.subject_genre_id = claim.subject_genre_id
    record.target_genre_id = claim.target_genre_id
    record.relation_type = claim.relation_type.value
    record.editorial_status = claim.editorial_status.value
    record.evidence_status = claim.evidence_status.value
    record.explanation = claim.explanation
    record.period_label = period.label if period is not None else None
    record.period_start_year = start.year if start is not None else None
    record.period_start_precision = start.precision.value if start is not None else None
    record.period_end_year = end.year if end is not None else None
    record.period_end_precision = end.precision.value if end is not None else None
    record.geography_summary = claim.geographic.summary if claim.geographic is not None else None
    record.provenance_summary = claim.provenance.summary if claim.provenance is not None else None


def _temporal(record: GenreRelationClaimRecord) -> HistoricalPeriod | None:
    if record.period_label is None:
        return None
    start = _bound(record.period_start_year, record.period_start_precision)
    end = _bound(record.period_end_year, record.period_end_precision)
    return HistoricalPeriod(label=record.period_label, start=start, end=end)


def _bound(year: int | None, precision: str | None) -> TemporalBound | None:
    if year is None or precision is None:
        return None
    return TemporalBound(year=year, precision=TemporalPrecision(precision))


def recording_origin_claim_from_records(
    record: RecordingOriginClaimRecord,
    evidence_records: list[RecordingOriginClaimEvidenceReferenceRecord],
) -> RecordingOriginClaim:
    return RecordingOriginClaim(
        id=record.id,
        recording_id=record.recording_id,
        work_id=record.work_id,
        predicate=RecordingOriginPredicate(record.predicate),
        editorial_status=EditorialStatus(record.editorial_status),
        evidence_status=EvidenceStatus(record.evidence_status),
        explanation=record.explanation,
        temporal=_recording_origin_temporal(record),
        geographic=GeographicContext(record.geography_summary) if record.geography_summary is not None else None,
        provenance=ClaimProvenance(record.provenance_summary) if record.provenance_summary is not None else None,
        evidence_references=tuple(
            ClaimEvidenceReference(
                source_fragment_id=item.source_fragment_id,
                role=EvidenceRole(item.role),
                locator_text=item.locator_text,
                external_url=item.external_url,
            )
            for item in evidence_records
        ),
    )


def record_from_recording_origin_claim(claim: RecordingOriginClaim) -> RecordingOriginClaimRecord:
    period = claim.temporal
    start = period.start if period is not None else None
    end = period.end if period is not None else None
    return RecordingOriginClaimRecord(
        id=claim.id,
        recording_id=claim.recording_id,
        work_id=claim.work_id,
        predicate=claim.predicate.value,
        editorial_status=claim.editorial_status.value,
        evidence_status=claim.evidence_status.value,
        explanation=claim.explanation,
        period_label=period.label if period is not None else None,
        period_start_year=start.year if start is not None else None,
        period_start_precision=start.precision.value if start is not None else None,
        period_end_year=end.year if end is not None else None,
        period_end_precision=end.precision.value if end is not None else None,
        geography_summary=claim.geographic.summary if claim.geographic is not None else None,
        provenance_summary=claim.provenance.summary if claim.provenance is not None else None,
    )


def evidence_records_from_recording_origin_claim(
    claim: RecordingOriginClaim,
) -> list[RecordingOriginClaimEvidenceReferenceRecord]:
    return [
        RecordingOriginClaimEvidenceReferenceRecord(
            id=uuid7(),
            claim_id=claim.id,
            source_fragment_id=reference.source_fragment_id,
            role=reference.role.value,
            locator_text=reference.locator_text,
            external_url=reference.external_url,
        )
        for reference in claim.evidence_references
    ]


def update_recording_origin_claim_record(
    record: RecordingOriginClaimRecord,
    claim: RecordingOriginClaim,
) -> None:
    period = claim.temporal
    start = period.start if period is not None else None
    end = period.end if period is not None else None
    record.recording_id = claim.recording_id
    record.work_id = claim.work_id
    record.predicate = claim.predicate.value
    record.editorial_status = claim.editorial_status.value
    record.evidence_status = claim.evidence_status.value
    record.explanation = claim.explanation
    record.period_label = period.label if period is not None else None
    record.period_start_year = start.year if start is not None else None
    record.period_start_precision = start.precision.value if start is not None else None
    record.period_end_year = end.year if end is not None else None
    record.period_end_precision = end.precision.value if end is not None else None
    record.geography_summary = claim.geographic.summary if claim.geographic is not None else None
    record.provenance_summary = claim.provenance.summary if claim.provenance is not None else None


def _recording_origin_temporal(record: RecordingOriginClaimRecord) -> HistoricalPeriod | None:
    if record.period_label is None:
        return None
    start = _bound(record.period_start_year, record.period_start_precision)
    end = _bound(record.period_end_year, record.period_end_precision)
    return HistoricalPeriod(label=record.period_label, start=start, end=end)
