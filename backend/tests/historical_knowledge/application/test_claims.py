from uuid import UUID

import pytest
from tests.historical_knowledge.fakes import (
    FakeGenreStatus,
    FakeHistoricalKnowledgeUnitOfWork,
    FakeSourceRepository,
)

from roots_of_rhythm.historical_knowledge.application import (
    ClaimService,
    EndpointGenreNotPublished,
    EvidenceFragmentNotReviewed,
    SourceService,
)
from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    GenreRelationClaim,
    GeographicContext,
    HistoricalPeriod,
    RelationType,
    SourceFragment,
    TemporalBound,
    TemporalPrecision,
)


@pytest.mark.asyncio
async def test_publish_requires_published_endpoints_and_reviewed_support() -> None:
    subject, target = UUID(int=10), UUID(int=20)
    claims: dict[UUID, GenreRelationClaim] = {}
    sources = FakeSourceRepository()
    genre_status = FakeGenreStatus(existing={subject, target})

    def uow_factory() -> FakeHistoricalKnowledgeUnitOfWork:
        return FakeHistoricalKnowledgeUnitOfWork(claims, sources)

    claim_service = ClaimService(uow_factory, genre_status)  # type: ignore[arg-type]
    source_service = SourceService(uow_factory)  # type: ignore[arg-type]

    source = await source_service.create_source("Smithsonian Music")
    version = await source_service.create_version(source.id, "v1")
    fragment = await source_service.create_fragment(version.id, locator_text="entry")

    claim = await claim_service.create_draft(subject, target, RelationType.DEVELOPED_FROM)
    claim = await claim_service.replace_content(
        claim.id,
        explanation="Swing developed from jazz.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        geographic=GeographicContext.create("United States"),
        provenance=ClaimProvenance.create("Seed research"),
        evidence_status=EvidenceStatus.SUPPORTED,
    )
    claim = await claim_service.replace_evidence(
        claim.id,
        (ClaimEvidenceReference.create(fragment.id, EvidenceRole.SUPPORTS, locator_text="entry"),),
    )

    with pytest.raises(EndpointGenreNotPublished):
        await claim_service.publish(claim.id)

    genre_status.published = {subject, target}
    with pytest.raises(EvidenceFragmentNotReviewed):
        await claim_service.publish(claim.id)

    await source_service.mark_fragment_reviewed(fragment.id)
    published = await claim_service.publish(claim.id)
    assert published.editorial_status.value == "published"

    genre_status.published = {subject}
    assert await claim_service.get_publicly_visible(published.id) is None
    genre_status.published = {subject, target}
    assert await claim_service.get_publicly_visible(published.id) is not None

    public_refs = await claim_service.public_evidence_references(published)
    assert len(public_refs) == 1
    sources.fragments[fragment.id] = SourceFragment(
        id=fragment.id,
        source_version_id=version.id,
        review_status=FragmentReviewStatus.PENDING,
        locator_text="entry",
    )
    assert await claim_service.public_evidence_references(published) == ()
