from typing import TYPE_CHECKING

import pytest

from roots_of_rhythm.historical_knowledge.domain import (
    EditorialStatus,
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    RelationType,
)
from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import (
    SqlAlchemyHistoricalKnowledgeUnitOfWork,
)
from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.music_catalog.domain import EditorialStatus as MusicEditorialStatus
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.seed import CorpusSeedRunner
from roots_of_rhythm.seed import genre_knowledge as data

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_genre_knowledge_seed(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    await CorpusSeedRunner(session_factory).run()

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        genres = [
            await uow.genres.get_published(genre_id)
            for genre_id in (data.JAZZ_ID, data.SWING_ID, data.JUMP_BLUES_ID, data.COUNTRY_ID, data.RHYTHM_AND_BLUES_ID)
        ]
    assert [genre.content.canonical_name for genre in genres if genre is not None] == [
        "Jazz",
        "Swing",
        "Jump Blues",
        "Country",
        "Rhythm and Blues",
    ]
    assert all(genre is not None and genre.editorial_status is MusicEditorialStatus.PUBLISHED for genre in genres)

    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(session_factory) as uow:
        developed = await uow.claims.get(data.SWING_FROM_JAZZ_CLAIM_ID)
        contributed = await uow.claims.get(data.SWING_TO_JUMP_CLAIM_ID)
        smithsonian = await uow.sources.get_source(data.SMITHSONIAN_SOURCE_ID)
        loc = await uow.sources.get_source(data.LOC_SOURCE_ID)
        fragments = [
            await uow.sources.get_fragment(fragment_id)
            for fragment_id in (
                data.JAZZ_INTRO_FRAGMENT_ID,
                data.JAZZ_BLUES_FRAGMENT_ID,
                data.FOLKLIFE_RNB_FRAGMENT_ID,
                data.LOC_RNB_FRAGMENT_ID,
            )
        ]

    assert developed is not None and developed.editorial_status is EditorialStatus.PUBLISHED
    assert developed.relation_type is RelationType.DEVELOPED_FROM
    assert developed.evidence_status is EvidenceStatus.SUPPORTED
    assert all(reference.role is EvidenceRole.SUPPORTS for reference in developed.evidence_references)
    assert contributed is not None and contributed.editorial_status is EditorialStatus.PUBLISHED
    assert contributed.relation_type is RelationType.CONTRIBUTED_TO_EMERGENCE_OF
    assert len(contributed.evidence_references) == 2
    assert smithsonian is not None and smithsonian.title == data.SMITHSONIAN_TITLE
    assert smithsonian.responsible_organization == data.SMITHSONIAN_RESPONSIBLE_ORGANIZATION
    assert smithsonian.external_url == data.SMITHSONIAN_EXTERNAL_URL
    assert loc is not None and loc.title == data.LOC_TITLE
    assert loc.responsible_organization == data.LOC_RESPONSIBLE_ORGANIZATION
    assert loc.external_url == data.LOC_EXTERNAL_URL
    assert all(fragment is not None for fragment in fragments)
    assert all(
        fragment.review_status is FragmentReviewStatus.REVIEWED for fragment in fragments if fragment is not None
    )
