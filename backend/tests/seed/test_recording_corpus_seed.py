from typing import TYPE_CHECKING

import pytest

from roots_of_rhythm.historical_knowledge.domain import (
    EditorialStatus as KnowledgeEditorialStatus,
)
from roots_of_rhythm.historical_knowledge.domain import (
    EvidenceStatus,
    FragmentReviewStatus,
    RecordingOriginPredicate,
)
from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import (
    SqlAlchemyHistoricalKnowledgeUnitOfWork,
)
from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.seed import CorpusSeedRunner
from roots_of_rhythm.seed import recording_corpus as data

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_recording_corpus_seed(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    await CorpusSeedRunner(session_factory).run()

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        recordings = [await uow.recordings.get_published(recording_id) for recording_id, _ in data.SEED_RECORDINGS]
        english = await uow.lyrics_versions.get_published(data.SIXTEEN_TONS_EN_LYRICS_ID)
        russian = await uow.lyrics_versions.get_published(data.SIXTEEN_TONS_RU_READING_ID)
        translation = await uow.lyrics_version_relations.get_published(data.SIXTEEN_TONS_TRANSLATION_RELATION_ID)
    assert [recording.recorded_period for recording in recordings if recording is not None] == [
        content.recorded_period for _, content in data.SEED_RECORDINGS
    ]
    assert all(recording is not None for recording in recordings)
    assert all(recording.is_published for recording in recordings if recording is not None)
    assert english is not None and english.body is None
    assert russian is not None and russian.body is None and russian.is_machine_translated
    assert translation is not None and translation.source_lyrics_version_id == data.SIXTEEN_TONS_RU_READING_ID

    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(session_factory) as uow:
        fragment = await uow.sources.get_fragment(data.SIXTEEN_TONS_FRAGMENT_ID)
        origin = await uow.recording_origin_claims.get(data.MERLE_FIRST_RECORDING_CLAIM_ID)
        guide = await uow.listening_guides.get(data.FORD_LISTENING_GUIDE_ID)
    assert fragment is not None and fragment.review_status is FragmentReviewStatus.REVIEWED
    assert origin is not None and origin.editorial_status is KnowledgeEditorialStatus.PUBLISHED
    assert origin.evidence_status is EvidenceStatus.SUPPORTED
    assert origin.predicate is RecordingOriginPredicate.FIRST_RECORDING_OF
    assert origin.recording_id == data.MERLE_TRAVIS_RECORDING_ID
    assert guide is not None and guide.editorial_status is KnowledgeEditorialStatus.PUBLISHED
    assert guide.recording_id == data.TENNESSEE_ERNIE_FORD_RECORDING_ID
    assert guide.observations == data.FORD_LISTENING_GUIDE.observations
