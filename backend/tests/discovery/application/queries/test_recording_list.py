from uuid import UUID, uuid7

import pytest

from roots_of_rhythm.discovery.application.queries.recording_list import RecordingListQuery
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
    Recording,
    RecordingContent,
    RecordingCredit,
    RecordingCreditTargetKind,
    RecordingWorkUsage,
    RecordingWorkUsageKind,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.music_catalog.public.recording_reader import RecordingListData
from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReadData
from tests.discovery.readers_stubs import StubPublishedPeopleReader, StubRecordingReader


def _genre(name: str) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Published definition."),
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
async def test_recording_list_query_projects_recordings_from_read_data() -> None:
    work_id = uuid7()
    group_id = uuid7()
    jazz = _genre("Jazz")
    group = Group.create(
        group_id,
        GroupContent.create("Dave Brubeck Quartet"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    visible = Recording.create(
        uuid7(),
        RecordingContent.create(
            "Take Five",
            recorded_period=ExistencePeriod.create(
                start=TemporalBound(1959, TemporalPrecision.EXACT_YEAR),
            ),
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
    assignment = _assignment(visible.id, jazz)
    list_data = RecordingListData(
        recordings=(visible,),
        assignments_by_recording={visible.id: (assignment,)},
        genres={jazz.id: jazz},
        groups={group.id: group},
        person_ids=frozenset(),
    )
    query = RecordingListQuery(
        StubRecordingReader(list_data=list_data),
        StubPublishedPeopleReader(PublishedPeopleReadData(persons=())),
    )

    response = await query.list()

    assert [item.title for item in response.items] == ["Take Five"]
    assert response.items[0].primary_credits[0].target.name == "Dave Brubeck Quartet"
    assert len(response.items[0].genres) == 1
    assert response.items[0].genres[0].name == "Jazz"


@pytest.mark.asyncio
async def test_recording_list_query_empty() -> None:
    empty = RecordingListData(
        recordings=(),
        assignments_by_recording={},
        genres={},
        groups={},
        person_ids=frozenset(),
    )
    query = RecordingListQuery(
        StubRecordingReader(list_data=empty),
        StubPublishedPeopleReader(PublishedPeopleReadData(persons=())),
    )

    response = await query.list()

    assert response.items == []
