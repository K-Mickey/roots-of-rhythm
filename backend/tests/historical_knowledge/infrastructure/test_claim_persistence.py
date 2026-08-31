from typing import TYPE_CHECKING

import pytest

from roots_of_rhythm.historical_knowledge.application import (
    CreateGenreRelationClaim,
    GenreRelationClaimService,
    PublishGenreRelationClaim,
    SourceService,
    UniqueConstraintViolation,
)
from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EvidenceRole,
    EvidenceStatus,
    GeographicContext,
    HistoricalPeriod,
    RelationType,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.historical_knowledge.infrastructure.claim_repository import SqlAlchemyClaimRepository
from roots_of_rhythm.historical_knowledge.infrastructure.genre_relation_claim_reader import (
    SqlAlchemyPublishedGenreRelationClaimReader,
)
from roots_of_rhythm.historical_knowledge.infrastructure.source_repository import SqlAlchemySourceRepository
from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import (
    SqlAlchemyHistoricalKnowledgeUnitOfWork,
)
from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.infrastructure.transaction import SqlAlchemyTransactionScope, sqlalchemy_session
from roots_of_rhythm.music_catalog.application import GenreService
from roots_of_rhythm.music_catalog.domain import ClassificationContent
from roots_of_rhythm.music_catalog.infrastructure.repository import SqlAlchemyGenreRepository
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

    from roots_of_rhythm.application.transaction import Transaction


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_claim_visibility_follows_endpoint_genre_publication(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    genre_service = GenreService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    jazz = await genre_service.create(ClassificationContent.create("Jazz", definition="Early jazz."))
    swing = await genre_service.create(ClassificationContent.create("Swing", definition="Big-band jazz."))
    await genre_service.publish(jazz.id)
    await genre_service.publish(swing.id)

    def hk_uow() -> SqlAlchemyHistoricalKnowledgeUnitOfWork:
        return SqlAlchemyHistoricalKnowledgeUnitOfWork(session_factory)

    transaction_scope = SqlAlchemyTransactionScope(session_factory)

    def claim_repository(transaction: "Transaction") -> SqlAlchemyClaimRepository:
        return SqlAlchemyClaimRepository(sqlalchemy_session(transaction))

    def source_repository(transaction: "Transaction") -> SqlAlchemySourceRepository:
        return SqlAlchemySourceRepository(sqlalchemy_session(transaction))

    def genre_repository(transaction: "Transaction") -> SqlAlchemyGenreRepository:
        return SqlAlchemyGenreRepository(sqlalchemy_session(transaction))

    claim_service = GenreRelationClaimService(
        transaction_scope,
        claim_repository,
        source_repository,
    )
    claim_reader = SqlAlchemyPublishedGenreRelationClaimReader(session_factory)
    create_claim = CreateGenreRelationClaim(transaction_scope, claim_repository, genre_repository)
    publish_claim = PublishGenreRelationClaim(
        transaction_scope,
        claim_repository,
        source_repository,
        genre_repository,
    )
    source_service = SourceService(hk_uow)

    source = await source_service.create_source(
        "Jazz",
        responsible_organization="Smithsonian Music",
        external_url="https://music.si.edu/story/jazz",
    )
    async with hk_uow() as uow:
        loaded = await uow.sources.get_source(source.id)
    assert loaded is not None
    assert loaded.title == "Jazz"
    assert loaded.responsible_organization == "Smithsonian Music"
    assert loaded.external_url == "https://music.si.edu/story/jazz"
    assert loaded.author is None
    assert loaded.publication is None
    assert loaded.publication_date is None
    version = await source_service.create_version(source.id, "catalog")
    fragment = await source_service.create_fragment(version.id, locator_text="Swing page")
    await source_service.mark_fragment_reviewed(fragment.id)

    claim = await create_claim.execute(swing.id, jazz.id, RelationType.DEVELOPED_FROM)
    claim = await claim_service.replace_content(
        claim.id,
        explanation="Swing developed from jazz practices.",
        temporal=HistoricalPeriod.create(
            "late 1920s–1940s",
            TemporalBound(1920, TemporalPrecision.LATE_DECADE),
            TemporalBound(1940, TemporalPrecision.DECADE),
        ),
        geographic=GeographicContext.create("United States"),
        provenance=ClaimProvenance.create("Institutional synthesis."),
        evidence_status=EvidenceStatus.SUPPORTED,
    )
    claim = await claim_service.replace_evidence(
        claim.id,
        (ClaimEvidenceReference.create(fragment.id, EvidenceRole.SUPPORTS, locator_text="Swing page"),),
    )
    published = await publish_claim.execute(claim.id)

    with pytest.raises(UniqueConstraintViolation):
        await create_claim.execute(swing.id, jazz.id, RelationType.DEVELOPED_FROM)

    public = await claim_reader.read_for_genre(swing.id)
    assert [item.id for item in public.claims] == [published.id]
    assert len(public.evidence_by_claim[published.id]) == 1

    await genre_service.archive(jazz.id)
    assert [item.id for item in (await claim_reader.read_for_genre(swing.id)).claims] == [published.id]

    await claim_service.archive(published.id)
    assert (await claim_reader.read_for_genre(swing.id)).claims == ()
