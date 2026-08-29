from uuid import UUID, uuid7

import pytest

from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    ClaimPublicationError,
    EditorialStatus,
    EvidenceRole,
    EvidenceStatus,
    GeographicContext,
    HistoricalPeriod,
    RecordingOriginClaim,
    RecordingOriginPredicate,
    TemporalBound,
    TemporalPrecision,
    is_recording_origin_badge_visible,
    origin_badge_values,
)


def _complete_claim(
    recording_id: UUID,
    work_id: UUID,
    predicate: RecordingOriginPredicate = RecordingOriginPredicate.FIRST_RECORDING_OF,
    *,
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED,
    references: tuple[ClaimEvidenceReference, ...] = (),
) -> RecordingOriginClaim:
    return (
        RecordingOriginClaim.create_draft(recording_id, work_id, predicate)
        .replace_content(
            explanation="Earliest known studio recording of the work.",
            temporal=HistoricalPeriod.create(
                "1946",
                TemporalBound(1946, TemporalPrecision.EXACT_YEAR),
            ),
            geographic=GeographicContext.create("United States"),
            provenance=ClaimProvenance.create("Editorial synthesis of institutional sources."),
            evidence_status=evidence_status,
        )
        .replace_evidence(references)
    )


def test_draft_requires_only_recording_work_and_predicate() -> None:
    recording_id, work_id = uuid7(), uuid7()
    claim = RecordingOriginClaim.create_draft(
        recording_id,
        work_id,
        RecordingOriginPredicate.FIRST_RELEASED_RECORDING_OF,
    )

    assert claim.editorial_status is EditorialStatus.DRAFT
    assert claim.evidence_status is EvidenceStatus.UNVERIFIED
    assert claim.explanation is None


def test_publish_requires_completeness_and_supported_evidence() -> None:
    recording_id, work_id, fragment = uuid7(), uuid7(), uuid7()
    draft = RecordingOriginClaim.create_draft(
        recording_id,
        work_id,
        RecordingOriginPredicate.FIRST_RECORDING_OF,
    )

    with pytest.raises(ClaimPublicationError) as incomplete:
        draft.publish()
    assert set(incomplete.value.missing_fields) >= {"explanation", "temporal", "geographic", "provenance"}

    supported = _complete_claim(recording_id, work_id, evidence_status=EvidenceStatus.SUPPORTED)
    with pytest.raises(ClaimPublicationError, match="supported_evidence"):
        supported.publish()

    published = supported.replace_evidence(
        (ClaimEvidenceReference.create(fragment, EvidenceRole.SUPPORTS, locator_text="p. 12"),)
    ).publish()
    assert published.editorial_status is EditorialStatus.PUBLISHED


def test_badge_visibility_requires_published_supported_endpoints() -> None:
    claim = _complete_claim(uuid7(), uuid7(), evidence_status=EvidenceStatus.SUPPORTED).replace_evidence(
        (ClaimEvidenceReference.create(uuid7(), EvidenceRole.SUPPORTS),)
    ).publish()

    assert is_recording_origin_badge_visible(
        claim,
        recording_published=True,
        work_published=True,
    )
    assert not is_recording_origin_badge_visible(
        claim,
        recording_published=False,
        work_published=True,
    )
    assert not is_recording_origin_badge_visible(
        claim.replace_content(evidence_status=EvidenceStatus.UNVERIFIED),
        recording_published=True,
        work_published=True,
    )
    assert not is_recording_origin_badge_visible(
        claim.archive(),
        recording_published=True,
        work_published=True,
    )


def test_replace_content_keeps_predicate_immutable() -> None:
    claim = RecordingOriginClaim.create_draft(
        uuid7(),
        uuid7(),
        RecordingOriginPredicate.FIRST_RECORDING_OF,
    )
    updated = claim.replace_content(explanation="Institutional sources confirm earliest studio take.")

    assert updated.predicate is RecordingOriginPredicate.FIRST_RECORDING_OF
    assert updated.explanation == "Institutional sources confirm earliest studio take."


def test_origin_badge_values_follow_predicate_enum_order() -> None:
    claims = (
        RecordingOriginClaim.create_draft(uuid7(), uuid7(), RecordingOriginPredicate.RECORDED_BY_WORK_AUTHOR),
        RecordingOriginClaim.create_draft(uuid7(), uuid7(), RecordingOriginPredicate.FIRST_RECORDING_OF),
        RecordingOriginClaim.create_draft(uuid7(), uuid7(), RecordingOriginPredicate.FIRST_RELEASED_RECORDING_OF),
        RecordingOriginClaim.create_draft(uuid7(), uuid7(), RecordingOriginPredicate.FIRST_RECORDING_OF),
    )

    assert origin_badge_values(claims) == [
        "first_recording_of",
        "first_released_recording_of",
        "recorded_by_work_author",
    ]
    assert origin_badge_values(()) == []


@pytest.mark.parametrize("predicate", list(RecordingOriginPredicate))
def test_all_origin_predicates_can_be_drafted(predicate: RecordingOriginPredicate) -> None:
    claim = RecordingOriginClaim.create_draft(uuid7(), uuid7(), predicate)
    assert claim.predicate is predicate
