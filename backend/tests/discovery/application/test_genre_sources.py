from uuid import UUID, uuid7

import pytest

from roots_of_rhythm.discovery.application.dto import GenreSourcesResponse
from roots_of_rhythm.discovery.application.errors import (
    GenreSourcesAssemblyError,
    GenreSourcesNotFound,
)
from roots_of_rhythm.discovery.application.genre_sources import GenreSourcesQuery
from roots_of_rhythm.historical_knowledge.application import ClaimService, SourceService
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
    RelationType,
    Source,
    SourceFragment,
    SourceVersion,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.music_catalog.domain import (
    ClassificationContent,
    Genre,
)
from roots_of_rhythm.music_catalog.domain import (
    EditorialStatus as GenreEditorialStatus,
)
from tests.historical_knowledge.fakes import (
    FakeGenreStatus,
    FakeHistoricalKnowledgeUnitOfWork,
    FakeSourceRepository,
)
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork


def _published_genre(name: str, genre_id: UUID | None = None) -> Genre:
    return Genre(
        id=genre_id or uuid7(),
        content=ClassificationContent.create(name, definition=f"{name} definition"),
        editorial_status=GenreEditorialStatus.PUBLISHED,
    )


def _claim(
    *,
    subject: UUID,
    target: UUID,
    relation_type: RelationType,
    explanation: str,
    temporal: HistoricalPeriod | None,
    evidence: tuple[ClaimEvidenceReference, ...] = (),
    claim_id: UUID | None = None,
) -> GenreRelationClaim:
    return GenreRelationClaim(
        id=claim_id or uuid7(),
        subject_genre_id=subject,
        target_genre_id=target,
        relation_type=relation_type,
        editorial_status=EditorialStatus.PUBLISHED,
        evidence_status=EvidenceStatus.SUPPORTED,
        explanation=explanation,
        temporal=temporal,
        geographic=GeographicContext.create("United States"),
        provenance=ClaimProvenance.create("research"),
        evidence_references=evidence,
    )


def _reviewed_source(
    sources: FakeSourceRepository,
    *,
    title: str,
    responsible_organization: str | None = None,
    external_url: str | None = None,
) -> tuple[Source, SourceFragment]:
    source = Source.create(
        title,
        responsible_organization=responsible_organization,
        external_url=external_url,
        source_id=uuid7(),
    )
    version = SourceVersion.create(source.id, "v1", version_id=uuid7())
    fragment = SourceFragment(
        id=uuid7(),
        source_version_id=version.id,
        review_status=FragmentReviewStatus.REVIEWED,
        locator_text="locator",
        external_url=external_url,
    )
    sources.sources[source.id] = source
    sources.versions[version.id] = version
    sources.fragments[fragment.id] = fragment
    return source, fragment


def _query(
    music: dict[UUID, Genre],
    claims: dict[UUID, GenreRelationClaim],
    sources: FakeSourceRepository,
    *,
    published: set[UUID] | None = None,
) -> GenreSourcesQuery:
    def uow_factory() -> FakeHistoricalKnowledgeUnitOfWork:
        return FakeHistoricalKnowledgeUnitOfWork(claims, sources)

    return GenreSourcesQuery(
        lambda: FakeMusicCatalogUnitOfWork(music),
        ClaimService(uow_factory, FakeGenreStatus(published=published or set(music))),  # type: ignore[arg-type]
        SourceService(uow_factory),  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_sources_query_returns_empty_for_published_genre_without_relations() -> None:
    swing = _published_genre("Swing")
    query = _query({swing.id: swing}, {}, FakeSourceRepository())

    response = await query.get(swing.id)

    assert response == GenreSourcesResponse(genre_id=str(swing.id), sources=[])


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [None, GenreEditorialStatus.DRAFT, GenreEditorialStatus.ARCHIVED])
async def test_sources_query_hides_missing_and_non_public_genres(status: GenreEditorialStatus | None) -> None:
    genre_id = uuid7()
    genres = (
        {}
        if status is None
        else {
            genre_id: Genre(
                id=genre_id,
                content=ClassificationContent.create("Hidden", definition="x"),
                editorial_status=status,
            )
        }
    )
    query = _query(genres, {}, FakeSourceRepository(), published=set())

    with pytest.raises(GenreSourcesNotFound):
        await query.get(genre_id)


@pytest.mark.asyncio
async def test_sources_query_deduplicates_and_orders_by_first_citation() -> None:
    swing = _published_genre("Swing")
    jazz = _published_genre("Jazz")
    jump = _published_genre("Jump Blues")
    sources = FakeSourceRepository()
    smithsonian, smithsonian_fragment = _reviewed_source(
        sources,
        title="Jazz",
        responsible_organization="Smithsonian Music",
        external_url="https://music.si.edu/story/jazz",
    )
    smithsonian_version_id = next(
        version.id for version in sources.versions.values() if version.source_id == smithsonian.id
    )
    smithsonian_second = SourceFragment(
        id=uuid7(),
        source_version_id=smithsonian_version_id,
        review_status=FragmentReviewStatus.REVIEWED,
    )
    sources.fragments[smithsonian_second.id] = smithsonian_second
    loc, loc_fragment = _reviewed_source(
        sources,
        title="Rhythm and Blues",
        responsible_organization="Library of Congress",
        external_url="https://www.loc.gov/rnb",
    )

    earlier = _claim(
        subject=swing.id,
        target=jazz.id,
        relation_type=RelationType.DEVELOPED_FROM,
        explanation="Swing developed from Jazz.",
        temporal=HistoricalPeriod.create(
            "late 1920s–1930s",
            TemporalBound(1920, TemporalPrecision.LATE_DECADE),
            TemporalBound(1930, TemporalPrecision.DECADE),
        ),
        evidence=(
            ClaimEvidenceReference.create(smithsonian_fragment.id, EvidenceRole.SUPPORTS),
            ClaimEvidenceReference.create(smithsonian_second.id, EvidenceRole.SUPPORTS),
        ),
    )
    later = _claim(
        subject=swing.id,
        target=jump.id,
        relation_type=RelationType.CONTRIBUTED_TO_EMERGENCE_OF,
        explanation="Swing contributed to Jump Blues.",
        temporal=HistoricalPeriod.create(
            "late 1930s–1940s",
            TemporalBound(1930, TemporalPrecision.LATE_DECADE),
            TemporalBound(1940, TemporalPrecision.DECADE),
        ),
        evidence=(
            ClaimEvidenceReference.create(smithsonian_fragment.id, EvidenceRole.SUPPORTS),
            ClaimEvidenceReference.create(loc_fragment.id, EvidenceRole.SUPPORTS),
        ),
    )
    music = {swing.id: swing, jazz.id: jazz, jump.id: jump}
    query = _query(music, {earlier.id: earlier, later.id: later}, sources)

    response = await query.get(swing.id)

    assert [item.id for item in response.sources] == [str(smithsonian.id), str(loc.id)]
    assert response.sources[0].title == "Jazz"
    assert response.sources[0].responsible_organization == "Smithsonian Music"
    assert response.sources[0].external_url == "https://music.si.edu/story/jazz"
    assert response.sources[1].title == "Rhythm and Blues"


@pytest.mark.asyncio
async def test_sources_query_filters_non_reviewed_fragments() -> None:
    swing = _published_genre("Swing")
    jazz = _published_genre("Jazz")
    sources = FakeSourceRepository()
    source = Source.create("Archive", source_id=uuid7())
    version = SourceVersion.create(source.id, "v1", version_id=uuid7())
    pending = SourceFragment(
        id=uuid7(),
        source_version_id=version.id,
        review_status=FragmentReviewStatus.PENDING,
    )
    sources.sources[source.id] = source
    sources.versions[version.id] = version
    sources.fragments[pending.id] = pending
    claim = _claim(
        subject=swing.id,
        target=jazz.id,
        relation_type=RelationType.DEVELOPED_FROM,
        explanation="Unreviewed only.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence=(ClaimEvidenceReference.create(pending.id, EvidenceRole.SUPPORTS),),
    )
    query = _query({swing.id: swing, jazz.id: jazz}, {claim.id: claim}, sources)

    response = await query.get(swing.id)

    assert response.sources == []


@pytest.mark.asyncio
async def test_sources_query_missing_source_is_assembly_error() -> None:
    swing = _published_genre("Swing")
    jazz = _published_genre("Jazz")
    sources = FakeSourceRepository()
    source, fragment = _reviewed_source(sources, title="Gone")
    claim = _claim(
        subject=swing.id,
        target=jazz.id,
        relation_type=RelationType.DEVELOPED_FROM,
        explanation="Missing source row.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence=(ClaimEvidenceReference.create(fragment.id, EvidenceRole.SUPPORTS),),
    )
    sources.sources.pop(source.id)
    query = _query({swing.id: swing, jazz.id: jazz}, {claim.id: claim}, sources)

    with pytest.raises(GenreSourcesAssemblyError):
        await query.get(swing.id)
