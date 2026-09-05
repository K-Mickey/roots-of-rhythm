from uuid import UUID, uuid7

import pytest
from tests.music_catalog.fakes import (
    FakeClassificationAssignmentRepository,
    FakeGenreRepository,
    FakeGroupRepository,
    FakeMusicalWorkRepository,
    FakeRecordingRepository,
)
from tests.support.scopes import fake_transaction_scope

from roots_of_rhythm.music_catalog.application.read_services.recordings import RecordingReadService
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    ClassificationAssignment,
    ClassificationContent,
    ClassificationTargetKind,
    EditorialStatus,
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
    WorkContent,
)


def _genre(name: str) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Published definition."),
        editorial_status=EditorialStatus.PUBLISHED,
    )


def _recording(work_id: UUID, group_id: UUID, *, title: str = "Take Five") -> Recording:
    return Recording.create(
        uuid7(),
        RecordingContent.create(
            title,
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


def _assignment(recording_id: UUID, genre: Genre) -> ClassificationAssignment:
    return ClassificationAssignment(
        id=uuid7(),
        target_kind=ClassificationTargetKind.RECORDING,
        target_id=recording_id,
        concept_id=genre.id,
        explanation="Explanation.",
        provenance="Editorial review.",
        editorial_status=EditorialStatus.PUBLISHED,
    )


@pytest.mark.asyncio
async def test_recording_read_service_list_overview_assembles_assignments_genres_groups() -> None:
    work_id = uuid7()
    group_id = uuid7()
    jazz = _genre("Jazz")
    group = Group.create(
        group_id,
        GroupContent.create("Dave Brubeck Quartet"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    recording = _recording(work_id, group_id)
    assignment = _assignment(recording.id, jazz)
    scope = fake_transaction_scope()
    service = RecordingReadService(
        scope,
        lambda _t: FakeRecordingRepository({recording.id: recording}),
        lambda _t: FakeClassificationAssignmentRepository({assignment.id: assignment}),
        lambda _t: FakeMusicalWorkRepository({}),
        lambda _t: FakeGenreRepository({jazz.id: jazz}),
        lambda _t: FakeGroupRepository({group.id: group}),
    )

    result = await service.list_overview()

    assert [item.id for item in result.recordings] == [recording.id]
    assert result.assignments_by_recording[recording.id] == (assignment,)
    assert set(result.genres.keys()) == {jazz.id}
    assert set(result.groups.keys()) == {group.id}
    assert result.person_ids == frozenset()


@pytest.mark.asyncio
async def test_recording_read_service_get_overview_assembles_works_assignments_genres_groups() -> None:
    work_id = uuid7()
    group_id = uuid7()
    jazz = _genre("Jazz")
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
    recording = _recording(work_id, group_id)
    assignment = _assignment(recording.id, jazz)
    scope = fake_transaction_scope()
    service = RecordingReadService(
        scope,
        lambda _t: FakeRecordingRepository({recording.id: recording}),
        lambda _t: FakeClassificationAssignmentRepository({assignment.id: assignment}),
        lambda _t: FakeMusicalWorkRepository({work.id: work}),
        lambda _t: FakeGenreRepository({jazz.id: jazz}),
        lambda _t: FakeGroupRepository({group.id: group}),
    )

    result = await service.get_recording_overview(recording.id)

    assert result.recording is recording
    assert set(result.works.keys()) == {work.id}
    assert result.assignments == (assignment,)
    assert set(result.genres.keys()) == {jazz.id}
    assert set(result.groups.keys()) == {group.id}


@pytest.mark.asyncio
async def test_recording_read_service_get_overview_missing_recording() -> None:
    service = RecordingReadService(
        fake_transaction_scope(),
        lambda _t: FakeRecordingRepository({}),
        lambda _t: FakeClassificationAssignmentRepository({}),
        lambda _t: FakeMusicalWorkRepository({}),
        lambda _t: FakeGenreRepository({}),
        lambda _t: FakeGroupRepository({}),
    )

    result = await service.get_recording_overview(uuid7())

    assert result.recording is None
    assert result.works == {}
