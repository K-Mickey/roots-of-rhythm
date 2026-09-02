from uuid import UUID, uuid7

import pytest

from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    ClaimPublicationError,
    EvidenceRole,
    EvidenceStatus,
    GenreRelationClaim,
    GeographicContext,
    HistoricalKnowledgeDomainError,
    HistoricalPeriod,
    RelationType,
    Source,
    SourceFragment,
    SourceVersion,
    TemporalBound,
    TemporalPrecision,
    canonicalize_relation_endpoints,
    is_claim_publicly_visible,
)


def _complete_claim(
    subject: UUID,
    target: UUID,
    relation_type: RelationType = RelationType.DEVELOPED_FROM,
    *,
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED,
    references: tuple[ClaimEvidenceReference, ...] = (),
) -> GenreRelationClaim:
    return (
        GenreRelationClaim.create_draft(subject, target, relation_type)
        .replace_content(
            explanation="Swing developed from earlier jazz practices.",
            temporal=HistoricalPeriod.create(
                "late 1920s–1940s",
                TemporalBound(1920, TemporalPrecision.LATE_DECADE),
                TemporalBound(1940, TemporalPrecision.DECADE),
            ),
            geographic=GeographicContext.create("United States"),
            provenance=ClaimProvenance.create("Editorial synthesis of institutional sources."),
            evidence_status=evidence_status,
        )
        .replace_evidence(references)
    )


def test_draft_requires_only_distinct_endpoints_and_type() -> None:
    subject, target = uuid7(), uuid7()
    claim = GenreRelationClaim.create_draft(subject, target, RelationType.INFLUENCED)

    assert claim.is_draft
    assert claim.is_unverified
    assert claim.explanation is None
    assert claim.evidence_references == ()


def test_overlaps_with_uses_canonical_id_order() -> None:
    lower = UUID(int=1)
    higher = UUID(int=2)

    forward = canonicalize_relation_endpoints(lower, higher, RelationType.OVERLAPS_WITH)
    swapped = canonicalize_relation_endpoints(higher, lower, RelationType.OVERLAPS_WITH)
    directed = canonicalize_relation_endpoints(higher, lower, RelationType.INFLUENCED)

    assert forward == swapped == (lower, higher)
    assert directed == (higher, lower)


def test_publish_requires_completeness_and_evidence_rules() -> None:
    subject, target, fragment = uuid7(), uuid7(), uuid7()
    draft = GenreRelationClaim.create_draft(subject, target, RelationType.DEVELOPED_FROM)

    with pytest.raises(ClaimPublicationError) as incomplete:
        draft.publish()
    assert set(incomplete.value.missing_fields) >= {"explanation", "temporal", "geographic", "provenance"}

    supported = _complete_claim(subject, target, evidence_status=EvidenceStatus.SUPPORTED)
    with pytest.raises(ClaimPublicationError, match="supported_evidence"):
        supported.publish()

    with_support = supported.replace_evidence(
        (ClaimEvidenceReference.create(fragment, EvidenceRole.SUPPORTS, locator_text="p. 12"),)
    )
    published = with_support.publish()
    assert published.is_published

    disputed = _complete_claim(
        subject,
        target,
        evidence_status=EvidenceStatus.DISPUTED,
        references=(ClaimEvidenceReference.create(fragment, EvidenceRole.SUPPORTS),),
    )
    with pytest.raises(ClaimPublicationError, match="opposing_evidence"):
        disputed.publish()


@pytest.mark.parametrize("relation_type", list(RelationType))
def test_all_relation_types_can_be_drafted(relation_type: RelationType) -> None:
    claim = GenreRelationClaim.create_draft(uuid7(), uuid7(), relation_type)
    assert claim.relation_type is relation_type


def test_public_visibility_requires_published_claim_and_endpoints() -> None:
    claim = _complete_claim(uuid7(), uuid7()).publish()
    assert is_claim_publicly_visible(claim, subject_published=True, target_published=True)
    assert not is_claim_publicly_visible(claim, subject_published=False, target_published=True)
    assert not is_claim_publicly_visible(claim.archive(), subject_published=True, target_published=True)


def test_source_fragment_review_lifecycle() -> None:
    source = Source.create("Jazz", responsible_organization="Smithsonian Music")
    version = SourceVersion.create(source.id, "2024 catalog")
    fragment = SourceFragment.create(version.id, locator_text="Swing entry")
    reviewed = fragment.mark_reviewed()

    assert fragment.review_status.value == "pending"
    assert reviewed.review_status.value == "reviewed"


def test_same_endpoint_ids_rejected() -> None:
    genre_id = uuid7()
    with pytest.raises(HistoricalKnowledgeDomainError, match="distinct"):
        GenreRelationClaim.create_draft(genre_id, genre_id, RelationType.OVERLAPS_WITH)
