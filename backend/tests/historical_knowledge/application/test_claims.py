from typing import Self
from uuid import UUID

import pytest

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
    Source,
    SourceFragment,
    SourceVersion,
    TemporalBound,
    TemporalPrecision,
)


class FakeGenreStatus:
    def __init__(self, published: set[UUID] | None = None, existing: set[UUID] | None = None) -> None:
        self.published = published or set()
        self.existing = existing if existing is not None else set(self.published)

    async def is_published(self, genre_id: UUID) -> bool:
        return genre_id in self.published

    async def exists(self, genre_id: UUID) -> bool:
        return genre_id in self.existing

    async def published_among(self, genre_ids: set[UUID]) -> set[UUID]:
        return {genre_id for genre_id in genre_ids if genre_id in self.published}


class FakeClaimRepository:
    def __init__(self, claims: dict[UUID, GenreRelationClaim]) -> None:
        self._claims = claims

    async def add(self, claim: GenreRelationClaim) -> None:
        self._claims[claim.id] = claim

    async def get(self, claim_id: UUID) -> GenreRelationClaim | None:
        return self._claims.get(claim_id)

    async def save(self, claim: GenreRelationClaim) -> None:
        self._claims[claim.id] = claim

    async def mark_deleted(self, claim_id: UUID) -> None:
        self._claims.pop(claim_id, None)

    async def list_by_genre(self, genre_id: UUID) -> list[GenreRelationClaim]:
        return [
            claim
            for claim in self._claims.values()
            if claim.subject_genre_id == genre_id or claim.target_genre_id == genre_id
        ]


class FakeSourceRepository:
    def __init__(self) -> None:
        self.sources: dict[UUID, Source] = {}
        self.versions: dict[UUID, SourceVersion] = {}
        self.fragments: dict[UUID, SourceFragment] = {}

    async def add_source(self, source: Source) -> None:
        self.sources[source.id] = source

    async def add_version(self, version: SourceVersion) -> None:
        self.versions[version.id] = version

    async def add_fragment(self, fragment: SourceFragment) -> None:
        self.fragments[fragment.id] = fragment

    async def get_source(self, source_id: UUID) -> Source | None:
        return self.sources.get(source_id)

    async def get_version(self, version_id: UUID) -> SourceVersion | None:
        return self.versions.get(version_id)

    async def get_fragment(self, fragment_id: UUID) -> SourceFragment | None:
        return self.fragments.get(fragment_id)

    async def save_fragment(self, fragment: SourceFragment) -> None:
        self.fragments[fragment.id] = fragment

    async def mark_source_deleted(self, source_id: UUID) -> None:
        self.sources.pop(source_id, None)
        version_ids = [version.id for version in self.versions.values() if version.source_id == source_id]
        for version_id in version_ids:
            self.versions.pop(version_id, None)
        for fragment_id, fragment in list(self.fragments.items()):
            if fragment.source_version_id in version_ids:
                self.fragments.pop(fragment_id, None)

    async def mark_version_deleted(self, version_id: UUID) -> None:
        self.versions.pop(version_id, None)
        for fragment_id, fragment in list(self.fragments.items()):
            if fragment.source_version_id == version_id:
                self.fragments.pop(fragment_id, None)

    async def mark_fragment_deleted(self, fragment_id: UUID) -> None:
        self.fragments.pop(fragment_id, None)


class FakeUnitOfWork:
    def __init__(self, claims: dict[UUID, GenreRelationClaim], sources: FakeSourceRepository) -> None:
        self.claims = FakeClaimRepository(claims)
        self.sources = sources
        self.commits = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        return None


@pytest.mark.asyncio
async def test_publish_requires_published_endpoints_and_reviewed_support() -> None:
    subject, target = UUID(int=10), UUID(int=20)
    claims: dict[UUID, GenreRelationClaim] = {}
    sources = FakeSourceRepository()
    genre_status = FakeGenreStatus(existing={subject, target})

    def uow_factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(claims, sources)

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
