from os import environ
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import delete

from roots_of_rhythm.historical_knowledge.application import ClaimService, SourceService
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
from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    ClaimEvidenceReferenceRecord,
    GenreRelationClaimRecord,
    SourceFragmentRecord,
    SourceRecord,
    SourceVersionRecord,
)
from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import (
    SqlAlchemyHistoricalKnowledgeUnitOfWork,
)
from roots_of_rhythm.infrastructure.database import create_database_engine, create_session_factory
from roots_of_rhythm.music_catalog.application import GenreService
from roots_of_rhythm.music_catalog.domain import ClassificationContent
from roots_of_rhythm.music_catalog.infrastructure.models import ClassificationConceptRecord
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Collection
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

pytestmark = pytest.mark.integration


class SessionGenreStatusLookup:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def is_published(self, genre_id: UUID) -> bool:
        async with SqlAlchemyMusicCatalogUnitOfWork(self._session_factory) as uow:
            return await uow.genres.get_published(genre_id) is not None

    async def exists(self, genre_id: UUID) -> bool:
        async with SqlAlchemyMusicCatalogUnitOfWork(self._session_factory) as uow:
            return await uow.genres.get(genre_id) is not None

    async def published_among(self, genre_ids: Collection[UUID]) -> set[UUID]:
        async with SqlAlchemyMusicCatalogUnitOfWork(self._session_factory) as uow:
            return await uow.genres.published_among(genre_ids)


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    database_url = environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://roots:roots@127.0.0.1:5432/roots_of_rhythm",
    )
    database_engine = create_database_engine(database_url)
    async with database_engine.begin() as connection:
        await connection.execute(delete(ClaimEvidenceReferenceRecord))
        await connection.execute(delete(GenreRelationClaimRecord))
        await connection.execute(delete(SourceFragmentRecord))
        await connection.execute(delete(SourceVersionRecord))
        await connection.execute(delete(SourceRecord))
        await connection.execute(delete(ClassificationConceptRecord))
    yield database_engine
    async with database_engine.begin() as connection:
        await connection.execute(delete(ClaimEvidenceReferenceRecord))
        await connection.execute(delete(GenreRelationClaimRecord))
        await connection.execute(delete(SourceFragmentRecord))
        await connection.execute(delete(SourceVersionRecord))
        await connection.execute(delete(SourceRecord))
        await connection.execute(delete(ClassificationConceptRecord))
    await database_engine.dispose()


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

    claim_service = ClaimService(hk_uow, SessionGenreStatusLookup(session_factory))
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

    claim = await claim_service.create_draft(swing.id, jazz.id, RelationType.DEVELOPED_FROM)
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
    published = await claim_service.publish(claim.id)

    assert await claim_service.get_publicly_visible(published.id) is not None
    public = await claim_service.list_public_for_genre(swing.id)
    assert [item.id for item in public] == [published.id]
    assert len(await claim_service.public_evidence_references(published)) == 1

    await genre_service.archive(jazz.id)
    assert await claim_service.get_publicly_visible(published.id) is None
    assert await claim_service.list_public_for_genre(swing.id) == []

    await genre_service.publish(jazz.id)
    assert await claim_service.get_publicly_visible(published.id) is not None
