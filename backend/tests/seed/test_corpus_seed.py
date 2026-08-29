from typing import TYPE_CHECKING

import pytest
from sqlalchemy import func, select

from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    ClaimEvidenceReferenceRecord,
    GenreRelationClaimRecord,
    ListeningGuideRecord,
    ListeningObservationRecord,
    RecordingOriginClaimEvidenceReferenceRecord,
    RecordingOriginClaimRecord,
    SourceFragmentRecord,
    SourceRecord,
    SourceVersionRecord,
)
from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.music_catalog.infrastructure.models import (
    ClassificationAssignmentRecord,
    ClassificationConceptRecord,
    GroupMembershipRecord,
    GroupRecord,
    LyricsVersionRecord,
    LyricsVersionRelationRecord,
    MusicalWorkRecord,
    RecordingCreditRecord,
    RecordingLyricsUsageRecord,
    RecordingRecord,
    RecordingWorkUsageRecord,
    WorkCreditRecord,
)
from roots_of_rhythm.people_catalog.infrastructure.models import PersonRecord
from roots_of_rhythm.seed import CorpusSeedRunner

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


async def _counts(
    engine: AsyncEngine,
) -> tuple[int, ...]:
    async with engine.connect() as connection:
        genres = await connection.scalar(select(func.count()).select_from(ClassificationConceptRecord))
        persons = await connection.scalar(select(func.count()).select_from(PersonRecord))
        groups = await connection.scalar(select(func.count()).select_from(GroupRecord))
        memberships = await connection.scalar(select(func.count()).select_from(GroupMembershipRecord))
        assignments = await connection.scalar(select(func.count()).select_from(ClassificationAssignmentRecord))
        claims = await connection.scalar(select(func.count()).select_from(GenreRelationClaimRecord))
        sources = await connection.scalar(select(func.count()).select_from(SourceRecord))
        versions = await connection.scalar(select(func.count()).select_from(SourceVersionRecord))
        fragments = await connection.scalar(select(func.count()).select_from(SourceFragmentRecord))
        evidence = await connection.scalar(select(func.count()).select_from(ClaimEvidenceReferenceRecord))
        works = await connection.scalar(select(func.count()).select_from(MusicalWorkRecord))
        work_credits = await connection.scalar(select(func.count()).select_from(WorkCreditRecord))
        lyrics_versions = await connection.scalar(select(func.count()).select_from(LyricsVersionRecord))
        lyrics_relations = await connection.scalar(select(func.count()).select_from(LyricsVersionRelationRecord))
        recordings = await connection.scalar(select(func.count()).select_from(RecordingRecord))
        recording_credits = await connection.scalar(select(func.count()).select_from(RecordingCreditRecord))
        recording_work_usages = await connection.scalar(select(func.count()).select_from(RecordingWorkUsageRecord))
        recording_lyrics_usages = await connection.scalar(select(func.count()).select_from(RecordingLyricsUsageRecord))
        origin_claims = await connection.scalar(select(func.count()).select_from(RecordingOriginClaimRecord))
        origin_evidence = await connection.scalar(
            select(func.count()).select_from(RecordingOriginClaimEvidenceReferenceRecord)
        )
        listening_guides = await connection.scalar(select(func.count()).select_from(ListeningGuideRecord))
        listening_observations = await connection.scalar(select(func.count()).select_from(ListeningObservationRecord))
    return (
        int(genres or 0),
        int(persons or 0),
        int(groups or 0),
        int(memberships or 0),
        int(assignments or 0),
        int(claims or 0),
        int(sources or 0),
        int(versions or 0),
        int(fragments or 0),
        int(evidence or 0),
        int(works or 0),
        int(work_credits or 0),
        int(lyrics_versions or 0),
        int(lyrics_relations or 0),
        int(recordings or 0),
        int(recording_credits or 0),
        int(recording_work_usages or 0),
        int(recording_lyrics_usages or 0),
        int(origin_claims or 0),
        int(origin_evidence or 0),
        int(listening_guides or 0),
        int(listening_observations or 0),
    )


@pytest.mark.asyncio
async def test_corpus_seed_is_idempotent_and_exact(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    runner = CorpusSeedRunner(session_factory)

    await runner.run()
    first = await _counts(engine)
    await runner.run()
    second = await _counts(engine)

    assert first == second == (5, 12, 4, 4, 14, 2, 3, 3, 5, 4, 6, 7, 2, 1, 3, 3, 3, 1, 1, 1, 1, 1)

    async with engine.connect() as connection:
        tables = set(await connection.run_sync(lambda sync: sync.dialect.get_table_names(sync)))
    assert "performers" not in tables
    assert {
        "groups",
        "group_memberships",
        "musical_works",
        "work_credits",
        "recordings",
        "recording_credits",
        "recording_work_usages",
        "lyrics_versions",
    } <= tables
