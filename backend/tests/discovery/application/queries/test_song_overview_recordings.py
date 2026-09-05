from uuid import UUID, uuid7

import pytest

from roots_of_rhythm.discovery.application.queries.song_overview import SongOverviewQuery
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    ClassificationAssignment,
    ClassificationContent,
    ClassificationTargetKind,
    EditorialStatus,
    ExistencePeriod,
    Genre,
    Group,
    GroupContent,
    MusicalWork,
    Recording,
    RecordingContent,
    RecordingCredit,
    RecordingCreditTargetKind,
    RecordingWorkUsage,
    RecordingWorkUsageKind,
    TemporalBound,
    TemporalPrecision,
    WorkContent,
)
from roots_of_rhythm.music_catalog.public.song_overview_reader import SongMusicReadData
from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReadData
from tests.discovery.readers_stubs import (
    StubPublishedPeopleReader,
    StubSongHistoricalKnowledgeReader,
    StubSongMusicReader,
)


def _genre(name: str) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Published definition."),
        editorial_status=EditorialStatus.PUBLISHED,
    )


def _recording(
    work_id: UUID,
    *,
    title: str,
    group: Group,
    usage_kind: RecordingWorkUsageKind,
    period: ExistencePeriod | None = None,
) -> Recording:
    return Recording.create(
        uuid7(),
        RecordingContent.create(
            title,
            recorded_period=period,
            recording_credits=(
                RecordingCredit.create(
                    uuid7(),
                    RecordingCreditTargetKind.GROUP,
                    group.id,
                    BillingRole.PRIMARY,
                ),
            ),
            work_usages=(RecordingWorkUsage.create(uuid7(), work_id, usage_kind),),
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )


def _assignment(recording_id: UUID, genre: Genre) -> ClassificationAssignment:
    return ClassificationAssignment(
        id=uuid7(),
        target_kind=ClassificationTargetKind.RECORDING,
        target_id=recording_id,
        concept_id=genre.id,
        explanation="Classification explanation.",
        provenance="Editorial review.",
        editorial_status=EditorialStatus.PUBLISHED,
    )


@pytest.mark.asyncio
async def test_song_overview_builds_recording_facets_and_chronology() -> None:
    work_id = uuid7()
    jazz = _genre("Jazz")
    swing = _genre("Swing")
    work = MusicalWork.create(
        work_id,
        WorkContent.create("Take Five"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    group = Group.create(
        uuid7(),
        GroupContent.create("Dave Brubeck Quartet"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    draft_group = Group.create(
        uuid7(),
        GroupContent.create("Draft Group"),
        editorial_status=EditorialStatus.DRAFT,
    )
    older = _recording(
        work_id,
        title="Older Take",
        group=group,
        usage_kind=RecordingWorkUsageKind.COMPLETE,
        period=ExistencePeriod.create(start=TemporalBound(1958, TemporalPrecision.EXACT_YEAR)),
    )
    newer = _recording(
        work_id,
        title="Newer Take",
        group=group,
        usage_kind=RecordingWorkUsageKind.PARTIAL,
        period=ExistencePeriod.create(start=TemporalBound(1960, TemporalPrecision.EXACT_YEAR)),
    )
    medley = _recording(
        work_id,
        title="Medley Night",
        group=group,
        usage_kind=RecordingWorkUsageKind.MEDLEY_COMPONENT,
    )
    hidden_primary = _recording(
        work_id,
        title="Hidden Primary",
        group=draft_group,
        usage_kind=RecordingWorkUsageKind.COMPLETE,
    )
    first_jazz = _assignment(older.id, jazz)
    second_jazz = _assignment(older.id, jazz)
    swing_assignment = _assignment(newer.id, swing)
    medley_jazz = _assignment(medley.id, jazz)
    hidden_jazz = _assignment(hidden_primary.id, jazz)
    query = SongOverviewQuery(
        StubSongMusicReader(
            SongMusicReadData(
                work,
                recordings=(older, newer, medley, hidden_primary),
                recording_assignments=(first_jazz, second_jazz, swing_assignment, medley_jazz, hidden_jazz),
                recording_genres=(jazz, swing),
                groups=(group,),
            )
        ),
        StubPublishedPeopleReader(PublishedPeopleReadData(())),
        StubSongHistoricalKnowledgeReader(),
    )

    response = await query.get(work_id)

    assert [(item.genre.name, item.recording_count) for item in response.recording_genres] == [
        ("Jazz", 1),
        ("Swing", 1),
    ]
    assert [item.title for item in response.recordings] == ["Older Take", "Newer Take", "Medley Night"]
    assert [item.work_usage_kind for item in response.recordings] == [
        RecordingWorkUsageKind.COMPLETE,
        RecordingWorkUsageKind.PARTIAL,
        RecordingWorkUsageKind.MEDLEY_COMPONENT,
    ]
    assert response.recordings[0].recorded_period.start is not None
    assert response.recordings[0].recorded_period.start.year == 1958
    assert response.recordings[0].origin_badges == []
    assert response.recordings[0].first_release_date is None
