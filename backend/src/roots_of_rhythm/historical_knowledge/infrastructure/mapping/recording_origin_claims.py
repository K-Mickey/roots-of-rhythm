from uuid import uuid7

from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EditorialStatus,
    EvidenceRole,
    EvidenceStatus,
    GeographicContext,
    HistoricalPeriod,
    RecordingOriginClaim,
    RecordingOriginPredicate,
)
from roots_of_rhythm.historical_knowledge.infrastructure.mapping._temporal import _bound
from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    RecordingOriginClaimEvidenceReferenceRecord,
    RecordingOriginClaimRecord,
)


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
