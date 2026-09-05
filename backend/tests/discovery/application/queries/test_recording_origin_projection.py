from uuid import UUID, uuid7

import pytest

from roots_of_rhythm.discovery.application.queries.recording_overview import RecordingOverviewQuery
from roots_of_rhythm.discovery.application.queries.song_overview import SongOverviewQuery
from roots_of_rhythm.historical_knowledge.domain import (
    EditorialStatus,
    EvidenceStatus,
    RecordingOriginClaim,
    RecordingOriginPredicate,
)
from roots_of_rhythm.historical_knowledge.public.recording_knowledge_reader import RecordingKnowledgeData
from roots_of_rhythm.historical_knowledge.public.song_context_reader import SongHistoricalKnowledgeReadData
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    Group,
    GroupContent,
    MusicalWork,
    Recording,
    RecordingContent,
    RecordingCredit,
    RecordingCreditTargetKind,
    RecordingWorkUsage,
    RecordingWorkUsageKind,
    WorkContent,
)
from roots_of_rhythm.music_catalog.domain import (
    EditorialStatus as MusicEditorialStatus,
)
from roots_of_rhythm.music_catalog.public.recording_lyrics_reader import RecordingLyricsProjection
from roots_of_rhythm.music_catalog.public.recording_reader import RecordingOverviewData
from roots_of_rhythm.music_catalog.public.song_overview_reader import SongMusicReadData
from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReadData
from tests.discovery.application.queries.test_song_overview_recordings import (
    _assignment,
    _genre,
    _recording,
)
from tests.discovery.readers_stubs import (
    StubPublishedPeopleReader,
    StubRecordingKnowledgeReader,
    StubRecordingLyricsReader,
    StubRecordingReader,
    StubSongHistoricalKnowledgeReader,
    StubSongMusicReader,
)


def _published_origin_claim(
    recording_id: UUID,
    work_id: UUID,
    predicate: RecordingOriginPredicate,
    *,
    evidence_status: EvidenceStatus = EvidenceStatus.SUPPORTED,
    editorial_status: EditorialStatus = EditorialStatus.PUBLISHED,
) -> RecordingOriginClaim:
    return RecordingOriginClaim(
        id=uuid7(),
        recording_id=recording_id,
        work_id=work_id,
        predicate=predicate,
        editorial_status=editorial_status,
        evidence_status=evidence_status,
    )


def _overview_reader(
    recording: Recording,
    work: MusicalWork,
    group: Group,
    *,
    claims: tuple[RecordingOriginClaim, ...] = (),
) -> RecordingOverviewQuery:
    overview = RecordingOverviewData(
        recording=recording,
        works={work.id: work},
        assignments=(),
        genres={},
        groups={group.id: group},
        person_ids=frozenset(),
    )
    knowledge = RecordingKnowledgeData(listening_guide=None, origin_claims=claims, source_access_by_version=())
    return RecordingOverviewQuery(
        StubRecordingReader(overview_data=overview),
        StubPublishedPeopleReader(PublishedPeopleReadData(persons=())),
        StubRecordingLyricsReader(RecordingLyricsProjection(items=())),
        StubRecordingKnowledgeReader(knowledge),
    )


@pytest.mark.asyncio
async def test_recording_overview_shows_supported_origin_badges_for_published_work() -> None:
    work_id = uuid7()
    group_id = uuid7()
    recording_id = uuid7()
    work = MusicalWork.create(
        work_id,
        WorkContent.create("Sixteen Tons"),
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    group = Group.create(
        group_id,
        GroupContent.create("Merle Travis"),
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    recording = Recording.create(
        recording_id,
        RecordingContent.create(
            "Sixteen Tons",
            recording_credits=(
                RecordingCredit.create(
                    uuid7(),
                    RecordingCreditTargetKind.GROUP,
                    group_id,
                    BillingRole.PRIMARY,
                ),
            ),
            work_usages=(RecordingWorkUsage.create(uuid7(), work_id, RecordingWorkUsageKind.COMPLETE),),
        ),
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    query = _overview_reader(
        recording,
        work,
        group,
        claims=(_published_origin_claim(recording_id, work_id, RecordingOriginPredicate.FIRST_RECORDING_OF),),
    )

    response = await query.get(recording_id)

    assert response.origin_badges == ["first_recording_of"]


@pytest.mark.asyncio
async def test_song_overview_shows_origin_badges_only_for_current_work() -> None:
    work_id = uuid7()
    other_work_id = uuid7()
    jazz = _genre("Jazz")
    group = Group.create(
        uuid7(),
        GroupContent.create("Merle Travis"),
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    work = MusicalWork.create(
        work_id,
        WorkContent.create("Sixteen Tons"),
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    recording = _recording(
        work_id,
        title="Sixteen Tons",
        group=group,
        usage_kind=RecordingWorkUsageKind.COMPLETE,
    )
    assignment = _assignment(recording.id, jazz)
    claims = {
        recording.id: [
            _published_origin_claim(recording.id, work_id, RecordingOriginPredicate.FIRST_RECORDING_OF),
            _published_origin_claim(recording.id, other_work_id, RecordingOriginPredicate.RECORDED_BY_WORK_AUTHOR),
        ]
    }
    query = SongOverviewQuery(
        StubSongMusicReader(
            SongMusicReadData(
                work,
                recordings=(recording,),
                recording_assignments=(assignment,),
                recording_genres=(jazz,),
                groups=(group,),
            )
        ),
        StubPublishedPeopleReader(PublishedPeopleReadData(())),
        StubSongHistoricalKnowledgeReader(
            SongHistoricalKnowledgeReadData((), tuple(claim for items in claims.values() for claim in items)),
        ),
    )

    response = await query.get(work_id)

    assert response.recordings[0].origin_badges == ["first_recording_of"]
