from uuid import UUID, uuid7

import pytest
from tests.historical_knowledge.fakes import FakeClaimRepository, FakeSourceRepository
from tests.support.scopes import fake_transaction_scope

from roots_of_rhythm.historical_knowledge.application.read_services.genre_relation_claims import (
    GenreRelationClaimReadService,
)
from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EditorialStatus,
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    GenreRelationClaim,
    RelationType,
    Source,
    SourceFragment,
    SourceVersion,
)


def _claim(
    genre_id: UUID,
    *,
    published: bool = True,
    other: UUID | None = None,
) -> GenreRelationClaim:
    return GenreRelationClaim(
        id=uuid7(),
        subject_genre_id=genre_id,
        target_genre_id=other or uuid7(),
        relation_type=RelationType.DEVELOPED_FROM,
        explanation="Explanation.",
        provenance=ClaimProvenance.create("Editorial review."),
        evidence_status=EvidenceStatus.SUPPORTED,
        editorial_status=EditorialStatus.PUBLISHED if published else EditorialStatus.DRAFT,
    )


@pytest.mark.asyncio
async def test_relation_claim_read_service_returns_published_claims_with_reviewed_evidence() -> None:
    genre_id = uuid7()
    source = Source.create("Archive", source_id=uuid7())
    version = SourceVersion.create(source.id, "v1", version_id=uuid7())
    reviewed = SourceFragment(
        id=uuid7(),
        source_version_id=version.id,
        review_status=FragmentReviewStatus.REVIEWED,
    )
    pending = SourceFragment(
        id=uuid7(),
        source_version_id=version.id,
        review_status=FragmentReviewStatus.PENDING,
    )
    sources = FakeSourceRepository()
    sources.sources[source.id] = source
    sources.versions[version.id] = version
    sources.fragments[reviewed.id] = reviewed
    sources.fragments[pending.id] = pending
    published = GenreRelationClaim(
        id=uuid7(),
        subject_genre_id=genre_id,
        target_genre_id=uuid7(),
        relation_type=RelationType.DEVELOPED_FROM,
        explanation="Swing from Jazz.",
        provenance=ClaimProvenance.create("review"),
        evidence_status=EvidenceStatus.SUPPORTED,
        editorial_status=EditorialStatus.PUBLISHED,
        evidence_references=(
            ClaimEvidenceReference.create(reviewed.id, EvidenceRole.SUPPORTS),
            ClaimEvidenceReference.create(pending.id, EvidenceRole.SUPPORTS),
        ),
    )
    draft = _claim(genre_id, published=False)
    claims = FakeClaimRepository({published.id: published, draft.id: draft})
    service = GenreRelationClaimReadService(
        fake_transaction_scope(),
        lambda _t: claims,
        lambda _t: sources,
    )

    result = await service.read_for_genre(genre_id)

    assert [item.id for item in result.claims] == [published.id]
    evidence = result.evidence_by_claim[published.id]
    assert len(evidence) == 1
    assert evidence[0].source_id == source.id
