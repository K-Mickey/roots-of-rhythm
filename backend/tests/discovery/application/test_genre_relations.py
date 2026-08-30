from uuid import UUID, uuid7

import pytest

from roots_of_rhythm.discovery.application.dto.genres import GenreRelationsResponse
from roots_of_rhythm.discovery.application.errors.genres import (
    GenreRelationsAssemblyError,
    GenreRelationsNotFound,
)
from roots_of_rhythm.discovery.application.genre_relations import GenreRelationsQuery
from roots_of_rhythm.historical_knowledge.application import ClaimService
from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    GenreRelationClaim,
    HistoricalPeriod,
    RelationType,
    Source,
    SourceFragment,
    SourceVersion,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.music_catalog.domain import ClassificationContent, Genre
from roots_of_rhythm.music_catalog.domain import EditorialStatus as GenreEditorialStatus
from tests.discovery.builders import published_genre, published_relation_claim
from tests.historical_knowledge.fakes import FakeHistoricalKnowledgeUnitOfWork, FakeSourceRepository
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork
from tests.support.scopes import pair_scope


def _claim_service(
    claims: dict[UUID, GenreRelationClaim],
    sources: FakeSourceRepository,
    music: dict[UUID, Genre],
) -> ClaimService:
    return ClaimService(
        pair_scope(
            lambda: FakeHistoricalKnowledgeUnitOfWork(claims, sources),  # type: ignore[arg-type, return-value]
            lambda: FakeMusicCatalogUnitOfWork(music),
        )
    )


@pytest.mark.asyncio
async def test_relations_query_maps_perspective_sort_and_evidence() -> None:
    swing = published_genre("Swing")
    jazz = published_genre("Jazz")
    jump = published_genre("Jump Blues")
    source = Source.create("Smithsonian", source_id=uuid7())
    version = SourceVersion.create(source.id, "v1", version_id=uuid7())
    fragment = SourceFragment(
        id=uuid7(),
        source_version_id=version.id,
        review_status=FragmentReviewStatus.REVIEWED,
        locator_text="locator",
        external_url="https://example.com",
    )
    pending = SourceFragment(
        id=uuid7(),
        source_version_id=version.id,
        review_status=FragmentReviewStatus.PENDING,
    )
    sources = FakeSourceRepository()
    sources.sources[source.id] = source
    sources.versions[version.id] = version
    sources.fragments[fragment.id] = fragment
    sources.fragments[pending.id] = pending

    earlier = published_relation_claim(
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
            ClaimEvidenceReference.create(
                fragment.id,
                EvidenceRole.SUPPORTS,
                locator_text="locator",
                external_url="https://example.com",
            ),
            ClaimEvidenceReference.create(pending.id, EvidenceRole.SUPPORTS),
        ),
    )
    later = published_relation_claim(
        subject=swing.id,
        target=jump.id,
        relation_type=RelationType.CONTRIBUTED_TO_EMERGENCE_OF,
        explanation="Swing contributed to Jump Blues.",
        temporal=HistoricalPeriod.create(
            "late 1930s–1940s",
            TemporalBound(1930, TemporalPrecision.LATE_DECADE),
            TemporalBound(1940, TemporalPrecision.DECADE),
        ),
    )
    claims = {earlier.id: earlier, later.id: later}
    music = {swing.id: swing, jazz.id: jazz, jump.id: jump}
    claim_service = _claim_service(claims, sources, music)
    query = GenreRelationsQuery(lambda: FakeMusicCatalogUnitOfWork(music), claim_service)

    response = await query.get(swing.id)

    assert response.genre_id == str(swing.id)
    assert [item.related_genre.name for item in response.relations] == ["Jazz", "Jump Blues"]
    assert response.relations[0].relation_type == "developed_from"
    assert response.relations[0].perspective == "subject"
    assert response.relations[1].relation_type == "contributed_to_emergence_of"
    assert len(response.relations[0].evidence_references) == 1
    assert response.relations[0].evidence_references[0].source_id == str(source.id)
    assert response.relations[0].evidence_references[0].locator_text == "locator"


@pytest.mark.asyncio
async def test_relations_query_returns_empty_for_published_genre_without_relations() -> None:
    swing = published_genre("Swing")
    claim_service = _claim_service({}, FakeSourceRepository(), {swing.id: swing})
    query = GenreRelationsQuery(lambda: FakeMusicCatalogUnitOfWork({swing.id: swing}), claim_service)

    response = await query.get(swing.id)

    assert response == GenreRelationsResponse(genre_id=str(swing.id), relations=[])


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [None, GenreEditorialStatus.DRAFT, GenreEditorialStatus.ARCHIVED])
async def test_relations_query_hides_missing_and_non_public_genres(status: GenreEditorialStatus | None) -> None:
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
    claim_service = _claim_service({}, FakeSourceRepository(), genres)
    query = GenreRelationsQuery(lambda: FakeMusicCatalogUnitOfWork(genres), claim_service)

    with pytest.raises(GenreRelationsNotFound):
        await query.get(genre_id)


@pytest.mark.asyncio
async def test_relations_query_unverified_keeps_empty_evidence_references() -> None:
    swing = published_genre("Swing")
    jazz = published_genre("Jazz")
    claim = published_relation_claim(
        subject=swing.id,
        target=jazz.id,
        relation_type=RelationType.DEVELOPED_FROM,
        explanation="Unverified relation.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    claim_service = _claim_service({claim.id: claim}, FakeSourceRepository(), {swing.id: swing, jazz.id: jazz})
    query = GenreRelationsQuery(
        lambda: FakeMusicCatalogUnitOfWork({swing.id: swing, jazz.id: jazz}),
        claim_service,
    )

    response = await query.get(swing.id)

    assert len(response.relations) == 1
    assert response.relations[0].evidence_status == "unverified"
    assert response.relations[0].evidence_references == []


@pytest.mark.asyncio
async def test_relations_query_maps_target_and_symmetric_perspectives() -> None:
    swing = published_genre("Swing")
    jazz = published_genre("Jazz")
    jump = published_genre("Jump Blues")
    target_claim = published_relation_claim(
        subject=jazz.id,
        target=swing.id,
        relation_type=RelationType.INFLUENCED,
        explanation="Jazz influenced Swing.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    symmetric_claim = published_relation_claim(
        subject=swing.id,
        target=jump.id,
        relation_type=RelationType.OVERLAPS_WITH,
        explanation="Swing overlaps with Jump Blues.",
        temporal=HistoricalPeriod.create("1940s", TemporalBound(1940, TemporalPrecision.DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    claims = {target_claim.id: target_claim, symmetric_claim.id: symmetric_claim}
    genres = {swing.id: swing, jazz.id: jazz, jump.id: jump}
    query = GenreRelationsQuery(
        lambda: FakeMusicCatalogUnitOfWork(genres),
        _claim_service(claims, FakeSourceRepository(), genres),
    )

    response = await query.get(swing.id)
    perspectives = {relation.id: relation.perspective for relation in response.relations}

    assert perspectives == {
        str(target_claim.id): "target",
        str(symmetric_claim.id): "symmetric",
    }


@pytest.mark.asyncio
async def test_relations_query_sorts_by_period_precision_type_name_and_null_last() -> None:
    swing = published_genre("Swing")
    related = [
        published_genre("Zulu"),
        published_genre("alpha"),
        published_genre("Beta"),
        published_genre("Early"),
        published_genre("No period"),
    ]
    decade_influenced = published_relation_claim(
        subject=swing.id,
        target=related[0].id,
        relation_type=RelationType.INFLUENCED,
        explanation="Decade influenced.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    decade_developed_alpha = published_relation_claim(
        subject=swing.id,
        target=related[1].id,
        relation_type=RelationType.DEVELOPED_FROM,
        explanation="Decade developed alpha.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    decade_developed_beta = published_relation_claim(
        subject=swing.id,
        target=related[2].id,
        relation_type=RelationType.DEVELOPED_FROM,
        explanation="Decade developed Beta.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    early = published_relation_claim(
        subject=swing.id,
        target=related[3].id,
        relation_type=RelationType.INFLUENCED,
        explanation="Early decade.",
        temporal=HistoricalPeriod.create("early 1930s", TemporalBound(1930, TemporalPrecision.EARLY_DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    no_period = published_relation_claim(
        subject=swing.id,
        target=related[4].id,
        relation_type=RelationType.INFLUENCED,
        explanation="No period.",
        temporal=None,
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    claims = {
        claim.id: claim
        for claim in (
            no_period,
            early,
            decade_developed_beta,
            decade_developed_alpha,
            decade_influenced,
        )
    }
    genres = {genre.id: genre for genre in (swing, *related)}
    query = GenreRelationsQuery(
        lambda: FakeMusicCatalogUnitOfWork(genres),
        _claim_service(claims, FakeSourceRepository(), genres),
    )

    response = await query.get(swing.id)

    assert [relation.related_genre.name for relation in response.relations] == [
        "Zulu",
        "alpha",
        "Beta",
        "Early",
        "No period",
    ]


@pytest.mark.asyncio
async def test_relations_query_maps_disputed_reviewed_evidence() -> None:
    swing = published_genre("Swing")
    jazz = published_genre("Jazz")
    source = Source.create("Archive")
    version = SourceVersion.create(source.id, "v1")
    fragment = SourceFragment.create(version.id).mark_reviewed()
    sources = FakeSourceRepository()
    sources.sources[source.id] = source
    sources.versions[version.id] = version
    sources.fragments[fragment.id] = fragment
    claim = published_relation_claim(
        subject=swing.id,
        target=jazz.id,
        relation_type=RelationType.DEVELOPED_FROM,
        explanation="Sources materially disagree.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence_status=EvidenceStatus.DISPUTED,
        evidence=(ClaimEvidenceReference.create(fragment.id, EvidenceRole.OPPOSES),),
    )
    genres = {swing.id: swing, jazz.id: jazz}
    query = GenreRelationsQuery(
        lambda: FakeMusicCatalogUnitOfWork(genres),
        _claim_service({claim.id: claim}, sources, genres),
    )

    response = await query.get(swing.id)

    assert response.relations[0].evidence_status == "disputed"
    assert response.relations[0].evidence_references[0].role == "opposes"


@pytest.mark.asyncio
async def test_relations_query_rejects_claim_unrelated_to_page_genre() -> None:
    swing = published_genre("Swing")
    jazz = published_genre("Jazz")
    blues = published_genre("Blues")
    unrelated = published_relation_claim(
        subject=jazz.id,
        target=blues.id,
        relation_type=RelationType.INFLUENCED,
        explanation="Jazz influenced Blues.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )

    class UnrelatedClaimService:
        async def list_public_for_genre(self, genre_id: UUID) -> list[GenreRelationClaim]:
            del genre_id
            return [unrelated]

        async def public_evidence_references_for_claims(
            self,
            claims: list[GenreRelationClaim],
        ) -> dict[UUID, tuple[object, ...]]:
            del claims
            return {}

    query = GenreRelationsQuery(
        lambda: FakeMusicCatalogUnitOfWork({swing.id: swing, jazz.id: jazz, blues.id: blues}),
        UnrelatedClaimService(),  # type: ignore[arg-type]
    )

    with pytest.raises(GenreRelationsAssemblyError):
        await query.get(swing.id)
