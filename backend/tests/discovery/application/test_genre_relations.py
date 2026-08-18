from uuid import UUID, uuid7

import pytest

from roots_of_rhythm.discovery.application.dto import GenreRelationsResponse
from roots_of_rhythm.discovery.application.errors import (
    GenreRelationsAssemblyError,
    GenreRelationsNotFound,
)
from roots_of_rhythm.discovery.application.genre_relations import GenreRelationsQuery
from roots_of_rhythm.historical_knowledge.application import ClaimService
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
    evidence_status: EvidenceStatus = EvidenceStatus.SUPPORTED,
    evidence: tuple[ClaimEvidenceReference, ...] = (),
    claim_id: UUID | None = None,
) -> GenreRelationClaim:
    return GenreRelationClaim(
        id=claim_id or uuid7(),
        subject_genre_id=subject,
        target_genre_id=target,
        relation_type=relation_type,
        editorial_status=EditorialStatus.PUBLISHED,
        evidence_status=evidence_status,
        explanation=explanation,
        temporal=temporal,
        geographic=GeographicContext.create("United States"),
        provenance=ClaimProvenance.create("research"),
        evidence_references=evidence,
    )


@pytest.mark.asyncio
async def test_relations_query_maps_perspective_sort_and_evidence() -> None:
    swing = _published_genre("Swing")
    jazz = _published_genre("Jazz")
    jump = _published_genre("Jump Blues")
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
            ClaimEvidenceReference.create(
                fragment.id,
                EvidenceRole.SUPPORTS,
                locator_text="locator",
                external_url="https://example.com",
            ),
            ClaimEvidenceReference.create(pending.id, EvidenceRole.SUPPORTS),
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
    )
    claims = {earlier.id: earlier, later.id: later}
    music = {swing.id: swing, jazz.id: jazz, jump.id: jump}
    claim_service = ClaimService(
        lambda: FakeHistoricalKnowledgeUnitOfWork(claims, sources),  # type: ignore[arg-type, return-value]
        FakeGenreStatus(published={swing.id, jazz.id, jump.id}),
    )
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
    swing = _published_genre("Swing")
    claim_service = ClaimService(
        lambda: FakeHistoricalKnowledgeUnitOfWork({}, FakeSourceRepository()),  # type: ignore[arg-type, return-value]
        FakeGenreStatus(published={swing.id}),
    )
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
    claim_service = ClaimService(
        lambda: FakeHistoricalKnowledgeUnitOfWork({}, FakeSourceRepository()),  # type: ignore[arg-type, return-value]
        FakeGenreStatus(),
    )
    query = GenreRelationsQuery(lambda: FakeMusicCatalogUnitOfWork(genres), claim_service)

    with pytest.raises(GenreRelationsNotFound):
        await query.get(genre_id)


@pytest.mark.asyncio
async def test_relations_query_unverified_keeps_empty_evidence_references() -> None:
    swing = _published_genre("Swing")
    jazz = _published_genre("Jazz")
    claim = _claim(
        subject=swing.id,
        target=jazz.id,
        relation_type=RelationType.DEVELOPED_FROM,
        explanation="Unverified relation.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    claim_service = ClaimService(
        lambda: FakeHistoricalKnowledgeUnitOfWork({claim.id: claim}, FakeSourceRepository()),  # type: ignore[arg-type, return-value]
        FakeGenreStatus(published={swing.id, jazz.id}),
    )
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
    swing = _published_genre("Swing")
    jazz = _published_genre("Jazz")
    jump = _published_genre("Jump Blues")
    target_claim = _claim(
        subject=jazz.id,
        target=swing.id,
        relation_type=RelationType.INFLUENCED,
        explanation="Jazz influenced Swing.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    symmetric_claim = _claim(
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
        ClaimService(
            lambda: FakeHistoricalKnowledgeUnitOfWork(claims, FakeSourceRepository()),  # type: ignore[arg-type, return-value]
            FakeGenreStatus(published=set(genres)),
        ),
    )

    response = await query.get(swing.id)
    perspectives = {relation.id: relation.perspective for relation in response.relations}

    assert perspectives == {
        str(target_claim.id): "target",
        str(symmetric_claim.id): "symmetric",
    }


@pytest.mark.asyncio
async def test_relations_query_sorts_by_period_precision_type_name_and_null_last() -> None:
    swing = _published_genre("Swing")
    related = [
        _published_genre("Zulu"),
        _published_genre("alpha"),
        _published_genre("Beta"),
        _published_genre("Early"),
        _published_genre("No period"),
    ]
    decade_influenced = _claim(
        subject=swing.id,
        target=related[0].id,
        relation_type=RelationType.INFLUENCED,
        explanation="Decade influenced.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    decade_developed_alpha = _claim(
        subject=swing.id,
        target=related[1].id,
        relation_type=RelationType.DEVELOPED_FROM,
        explanation="Decade developed alpha.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    decade_developed_beta = _claim(
        subject=swing.id,
        target=related[2].id,
        relation_type=RelationType.DEVELOPED_FROM,
        explanation="Decade developed Beta.",
        temporal=HistoricalPeriod.create("1930s", TemporalBound(1930, TemporalPrecision.DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    early = _claim(
        subject=swing.id,
        target=related[3].id,
        relation_type=RelationType.INFLUENCED,
        explanation="Early decade.",
        temporal=HistoricalPeriod.create("early 1930s", TemporalBound(1930, TemporalPrecision.EARLY_DECADE)),
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    no_period = _claim(
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
        ClaimService(
            lambda: FakeHistoricalKnowledgeUnitOfWork(claims, FakeSourceRepository()),  # type: ignore[arg-type, return-value]
            FakeGenreStatus(published=set(genres)),
        ),
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
    swing = _published_genre("Swing")
    jazz = _published_genre("Jazz")
    source = Source.create("Archive")
    version = SourceVersion.create(source.id, "v1")
    fragment = SourceFragment.create(version.id).mark_reviewed()
    sources = FakeSourceRepository()
    sources.sources[source.id] = source
    sources.versions[version.id] = version
    sources.fragments[fragment.id] = fragment
    claim = _claim(
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
        ClaimService(
            lambda: FakeHistoricalKnowledgeUnitOfWork({claim.id: claim}, sources),  # type: ignore[arg-type, return-value]
            FakeGenreStatus(published=set(genres)),
        ),
    )

    response = await query.get(swing.id)

    assert response.relations[0].evidence_status == "disputed"
    assert response.relations[0].evidence_references[0].role == "opposes"


@pytest.mark.asyncio
async def test_relations_query_rejects_claim_unrelated_to_page_genre() -> None:
    swing = _published_genre("Swing")
    jazz = _published_genre("Jazz")
    blues = _published_genre("Blues")
    unrelated = _claim(
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
