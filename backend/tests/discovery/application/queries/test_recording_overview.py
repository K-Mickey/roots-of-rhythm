from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.errors.recordings import RecordingOverviewNotFound
from roots_of_rhythm.discovery.application.queries.recording_overview import RecordingOverviewQuery
from roots_of_rhythm.historical_knowledge.public.recording_knowledge_reader import RecordingKnowledgeData
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    EditorialStatus,
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
from roots_of_rhythm.music_catalog.public.recording_lyrics_reader import (
    RecordingLyricsProjection,
)
from roots_of_rhythm.music_catalog.public.recording_reader import RecordingOverviewData
from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReadData
from tests.discovery.readers_stubs import (
    StubPublishedPeopleReader,
    StubRecordingKnowledgeReader,
    StubRecordingLyricsReader,
    StubRecordingReader,
)


@pytest.mark.asyncio
async def test_recording_overview_query_projects_published_recording() -> None:
    work_id = uuid7()
    group_id = uuid7()
    recording_id = uuid7()
    work = MusicalWork.create(
        work_id,
        WorkContent.create("Take Five"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    group = Group.create(
        group_id,
        GroupContent.create("Dave Brubeck Quartet"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    recording = Recording.create(
        recording_id,
        RecordingContent.create(
            "Take Five",
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
        editorial_status=EditorialStatus.PUBLISHED,
    )
    overview = RecordingOverviewData(
        recording=recording,
        works={work.id: work},
        assignments=(),
        genres={},
        groups={group.id: group},
        person_ids=frozenset(),
    )
    query = RecordingOverviewQuery(
        StubRecordingReader(overview_data=overview),
        StubPublishedPeopleReader(PublishedPeopleReadData(persons=())),
        StubRecordingLyricsReader(RecordingLyricsProjection(items=())),
        StubRecordingKnowledgeReader(
            RecordingKnowledgeData(listening_guide=None, origin_claims=(), source_access_by_version=())
        ),
    )

    response = await query.get(recording_id)

    assert response.id == str(recording_id)
    assert response.title == "Take Five"
    assert [item.work.name for item in response.works] == ["Take Five"]
    assert response.credits[0].target.name == "Dave Brubeck Quartet"
    assert response.origin_badges == []


@pytest.mark.asyncio
async def test_recording_overview_query_raises_when_read_data_missing_recording() -> None:
    overview = RecordingOverviewData(
        recording=None,
        works={},
        assignments=(),
        genres={},
        groups={},
        person_ids=frozenset(),
    )
    query = RecordingOverviewQuery(
        StubRecordingReader(overview_data=overview),
        StubPublishedPeopleReader(PublishedPeopleReadData(persons=())),
        StubRecordingLyricsReader(RecordingLyricsProjection(items=())),
        StubRecordingKnowledgeReader(
            RecordingKnowledgeData(listening_guide=None, origin_claims=(), source_access_by_version=())
        ),
    )

    with pytest.raises(RecordingOverviewNotFound):
        await query.get(uuid7())


@pytest.mark.asyncio
async def test_recording_overview_query_raises_when_no_published_works_remain() -> None:
    recording_id = uuid7()
    group_id = uuid7()
    recording = Recording.create(
        recording_id,
        RecordingContent.create(
            "Take Five",
            recording_credits=(
                RecordingCredit.create(
                    uuid7(),
                    RecordingCreditTargetKind.GROUP,
                    group_id,
                    BillingRole.PRIMARY,
                ),
            ),
            work_usages=(RecordingWorkUsage.create(uuid7(), uuid7(), RecordingWorkUsageKind.COMPLETE),),
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    overview = RecordingOverviewData(
        recording=recording,
        works={},
        assignments=(),
        genres={},
        groups={
            group_id: Group.create(
                group_id,
                GroupContent.create("Dave Brubeck Quartet"),
                editorial_status=EditorialStatus.PUBLISHED,
            )
        },
        person_ids=frozenset(),
    )
    query = RecordingOverviewQuery(
        StubRecordingReader(overview_data=overview),
        StubPublishedPeopleReader(PublishedPeopleReadData(persons=())),
        StubRecordingLyricsReader(RecordingLyricsProjection(items=())),
        StubRecordingKnowledgeReader(
            RecordingKnowledgeData(listening_guide=None, origin_claims=(), source_access_by_version=())
        ),
    )

    with pytest.raises(RecordingOverviewNotFound):
        await query.get(recording_id)
