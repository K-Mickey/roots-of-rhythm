from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from tests.historical_knowledge.fakes import FakeHistoricalKnowledgeUnitOfWork, FakeSourceRepository
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork

from roots_of_rhythm.historical_knowledge.application import (
    ClaimNotFound,
    CreateGenreRelationClaim,
    EndpointGenreMissing,
    EndpointGenreNotPublished,
    EvidenceFragmentNotReviewed,
    GenreRelationClaimService,
    PublishGenreRelationClaim,
    SourceService,
)
from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EvidenceRole,
    EvidenceStatus,
    GenreRelationClaim,
    GeographicContext,
    HistoricalPeriod,
    RelationType,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.music_catalog.domain import ClassificationContent, EditorialStatus, Genre

if TYPE_CHECKING:
    from roots_of_rhythm.application.transaction import Transaction
    from roots_of_rhythm.historical_knowledge.application.ports import ClaimRepository, SourceRepository
    from roots_of_rhythm.music_catalog.application.ports import GenreRepository


def _genre(genre_id: UUID, *, published: bool) -> Genre:
    status = EditorialStatus.PUBLISHED if published else EditorialStatus.DRAFT
    return Genre(id=genre_id, content=ClassificationContent.create(str(genre_id)), editorial_status=status)


def _operations(
    claims: dict[UUID, GenreRelationClaim],
    sources: FakeSourceRepository,
    genres: dict[UUID, Genre],
) -> tuple[
    GenreRelationClaimService,
    CreateGenreRelationClaim,
    PublishGenreRelationClaim,
    SourceService,
]:
    historical = FakeHistoricalKnowledgeUnitOfWork(claims, sources)
    music = FakeMusicCatalogUnitOfWork(genres)

    def transaction_scope() -> FakeHistoricalKnowledgeUnitOfWork:
        return historical

    def claim_repository(_transaction: "Transaction") -> "ClaimRepository":
        return historical.claims

    def source_repository(_transaction: "Transaction") -> "SourceRepository":
        return historical.sources

    def genre_repository(_transaction: "Transaction") -> "GenreRepository":
        return music.genres

    return (
        GenreRelationClaimService(
            transaction_scope,
            claim_repository,
            source_repository,
        ),
        CreateGenreRelationClaim(transaction_scope, claim_repository, genre_repository),
        PublishGenreRelationClaim(
            transaction_scope,
            claim_repository,
            source_repository,
            genre_repository,
        ),
        SourceService(lambda: historical),
    )


@pytest.mark.asyncio
async def test_publish_requires_published_endpoints_and_reviewed_support() -> None:
    subject, target = UUID(int=10), UUID(int=20)
    claims: dict[UUID, GenreRelationClaim] = {}
    sources = FakeSourceRepository()
    genres = {subject: _genre(subject, published=False), target: _genre(target, published=False)}
    claim_service, create_claim, publish_claim, source_service = _operations(claims, sources, genres)

    source = await source_service.create_source("Smithsonian Music")
    version = await source_service.create_version(source.id, "v1")
    fragment = await source_service.create_fragment(version.id, locator_text="entry")

    claim = await create_claim.execute(subject, target, RelationType.DEVELOPED_FROM)
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
        await publish_claim.execute(claim.id)

    genres[subject] = _genre(subject, published=True)
    genres[target] = _genre(target, published=True)
    with pytest.raises(EvidenceFragmentNotReviewed):
        await publish_claim.execute(claim.id)

    await source_service.mark_fragment_reviewed(fragment.id)
    published = await publish_claim.execute(claim.id)
    assert published.editorial_status.value == "published"

    archived = await claim_service.archive(published.id)
    assert archived.editorial_status.value == "archived"


@pytest.mark.asyncio
async def test_create_requires_both_genres() -> None:
    subject, target = UUID(int=10), UUID(int=20)
    claims: dict[UUID, GenreRelationClaim] = {}
    _service, create_claim, _publish_claim, _sources = _operations(
        claims,
        FakeSourceRepository(),
        {subject: _genre(subject, published=False)},
    )

    with pytest.raises(EndpointGenreMissing, match=str(target)):
        await create_claim.execute(subject, target, RelationType.DEVELOPED_FROM)

    assert claims == {}


@pytest.mark.asyncio
async def test_publish_reports_missing_claim() -> None:
    _service, _create_claim, publish_claim, _sources = _operations({}, FakeSourceRepository(), {})

    with pytest.raises(ClaimNotFound):
        await publish_claim.execute(UUID(int=10))
