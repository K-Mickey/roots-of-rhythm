from uuid import UUID

import pytest
from tests.historical_knowledge.fakes import FakeHistoricalKnowledgeUnitOfWork, FakeSourceRepository
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork
from tests.support.scopes import pair_scope

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
from roots_of_rhythm.music_catalog.domain import ClassificationContent, EditorialStatus, Genre


def _genre(genre_id: UUID, *, published: bool) -> Genre:
    status = EditorialStatus.PUBLISHED if published else EditorialStatus.DRAFT
    return Genre(id=genre_id, content=ClassificationContent.create(str(genre_id)), editorial_status=status)


@pytest.mark.asyncio
async def test_publish_requires_published_endpoints_and_reviewed_support() -> None:
    subject, target = UUID(int=10), UUID(int=20)
    claims: dict[UUID, GenreRelationClaim] = {}
    sources = FakeSourceRepository()
    genres = {subject: _genre(subject, published=False), target: _genre(target, published=False)}

    def uow_factory() -> FakeHistoricalKnowledgeUnitOfWork:
        return FakeHistoricalKnowledgeUnitOfWork(claims, sources)

    claim_service = ClaimService(
        pair_scope(uow_factory, lambda: FakeMusicCatalogUnitOfWork(genres)),  # type: ignore[arg-type]
    )
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

    genres[subject] = _genre(subject, published=True)
    genres[target] = _genre(target, published=True)
    with pytest.raises(EvidenceFragmentNotReviewed):
        await claim_service.publish(claim.id)

    await source_service.mark_fragment_reviewed(fragment.id)
    published = await claim_service.publish(claim.id)
    assert published.editorial_status.value == "published"

    genres[target] = _genre(target, published=False)
    assert await claim_service.get_publicly_visible(published.id) is None
    genres[target] = _genre(target, published=True)
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
