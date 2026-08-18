from os import environ
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import delete, func, select

from roots_of_rhythm.historical_knowledge.domain import (
    EditorialStatus as ClaimEditorialStatus,
)
from roots_of_rhythm.historical_knowledge.domain import (
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    RelationType,
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
from roots_of_rhythm.music_catalog.domain import EditorialStatus as GenreEditorialStatus
from roots_of_rhythm.music_catalog.infrastructure.models import ClassificationConceptRecord
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.seed import CorpusSeedRunner
from roots_of_rhythm.seed import corpus as data

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


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


async def _counts(engine: AsyncEngine) -> tuple[int, int, int, int, int, int]:
    async with engine.connect() as connection:
        genres = await connection.scalar(select(func.count()).select_from(ClassificationConceptRecord))
        claims = await connection.scalar(select(func.count()).select_from(GenreRelationClaimRecord))
        sources = await connection.scalar(select(func.count()).select_from(SourceRecord))
        versions = await connection.scalar(select(func.count()).select_from(SourceVersionRecord))
        fragments = await connection.scalar(select(func.count()).select_from(SourceFragmentRecord))
        evidence = await connection.scalar(select(func.count()).select_from(ClaimEvidenceReferenceRecord))
    return (
        int(genres or 0),
        int(claims or 0),
        int(sources or 0),
        int(versions or 0),
        int(fragments or 0),
        int(evidence or 0),
    )


@pytest.mark.asyncio
async def test_corpus_seed_is_idempotent_and_exact(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    runner = CorpusSeedRunner(session_factory)

    await runner.run()
    first = await _counts(engine)
    await runner.run()
    second = await _counts(engine)

    assert first == second == (3, 2, 2, 2, 4, 4)

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        jazz = await uow.genres.get_published(data.JAZZ_ID)
        swing = await uow.genres.get_published(data.SWING_ID)
        jump = await uow.genres.get_published(data.JUMP_BLUES_ID)

    assert jazz is not None and jazz.content.canonical_name == "Jazz"
    assert swing is not None and swing.content.canonical_name == "Swing"
    assert jump is not None and jump.content.canonical_name == "Jump Blues"
    assert {jazz.editorial_status, swing.editorial_status, jump.editorial_status} == {GenreEditorialStatus.PUBLISHED}

    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(session_factory) as uow:
        developed = await uow.claims.get(data.SWING_FROM_JAZZ_CLAIM_ID)
        contributed = await uow.claims.get(data.SWING_TO_JUMP_CLAIM_ID)
        smithsonian = await uow.sources.get_source(data.SMITHSONIAN_SOURCE_ID)
        loc = await uow.sources.get_source(data.LOC_SOURCE_ID)
        fragments = [
            await uow.sources.get_fragment(data.JAZZ_INTRO_FRAGMENT_ID),
            await uow.sources.get_fragment(data.JAZZ_BLUES_FRAGMENT_ID),
            await uow.sources.get_fragment(data.FOLKLIFE_RNB_FRAGMENT_ID),
            await uow.sources.get_fragment(data.LOC_RNB_FRAGMENT_ID),
        ]

    assert developed is not None
    assert developed.editorial_status is ClaimEditorialStatus.PUBLISHED
    assert developed.evidence_status is EvidenceStatus.SUPPORTED
    assert developed.relation_type is RelationType.DEVELOPED_FROM
    assert developed.subject_genre_id == data.SWING_ID
    assert developed.target_genre_id == data.JAZZ_ID
    assert all(ref.role is EvidenceRole.SUPPORTS for ref in developed.evidence_references)
    assert len(developed.evidence_references) == 2

    assert contributed is not None
    assert contributed.editorial_status is ClaimEditorialStatus.PUBLISHED
    assert contributed.evidence_status is EvidenceStatus.SUPPORTED
    assert contributed.relation_type is RelationType.CONTRIBUTED_TO_EMERGENCE_OF
    assert contributed.subject_genre_id == data.SWING_ID
    assert contributed.target_genre_id == data.JUMP_BLUES_ID
    assert len(contributed.evidence_references) == 2

    assert smithsonian is not None and smithsonian.title == data.SMITHSONIAN_TITLE
    assert smithsonian.responsible_organization == data.SMITHSONIAN_RESPONSIBLE_ORGANIZATION
    assert smithsonian.external_url == data.SMITHSONIAN_EXTERNAL_URL
    assert smithsonian.author is None
    assert smithsonian.publication is None
    assert smithsonian.publication_date is None
    assert loc is not None and loc.title == data.LOC_TITLE
    assert loc.responsible_organization == data.LOC_RESPONSIBLE_ORGANIZATION
    assert loc.external_url == data.LOC_EXTERNAL_URL
    assert loc.author is None
    assert loc.publication is None
    assert loc.publication_date is None
    assert all(
        fragment is not None and fragment.review_status is FragmentReviewStatus.REVIEWED for fragment in fragments
    )

    # Controlled corpus must not introduce Performer/Group/Recording persistence.
    async with engine.connect() as connection:
        tables = set(await connection.run_sync(lambda sync: sync.dialect.get_table_names(sync)))
    assert not {"performers", "groups", "recordings"} & tables
