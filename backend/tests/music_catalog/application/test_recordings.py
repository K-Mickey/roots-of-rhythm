from uuid import UUID, uuid7

import pytest
from tests.music_catalog.fakes import (
    FakeMusicalWorkRepository,
    FakeMusicCatalogUnitOfWork,
    FakeRecordingRepository,
)
from tests.people_catalog.fakes import FakePeopleCatalogUnitOfWork
from tests.support.scopes import pair_scope

from roots_of_rhythm.music_catalog.application import (
    RecordingPrimaryTargetNotPublished,
    RecordingService,
    RecordingWorkNotPublished,
)
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
from roots_of_rhythm.people_catalog.domain import EditorialStatus as PersonEditorialStatus
from roots_of_rhythm.people_catalog.domain import Person, PersonContent


def _content(
    work_id: UUID,
    target_id: UUID,
    *,
    target_kind: RecordingCreditTargetKind = RecordingCreditTargetKind.PERSON,
    additional_target_id: UUID | None = None,
) -> RecordingContent:
    recording_credits = [RecordingCredit.create(uuid7(), target_kind, target_id, BillingRole.PRIMARY)]
    if additional_target_id is not None:
        recording_credits.append(
            RecordingCredit.create(
                uuid7(),
                RecordingCreditTargetKind.PERSON,
                additional_target_id,
                BillingRole.ADDITIONAL,
            )
        )
    return RecordingContent.create(
        "Take",
        recording_credits=tuple(recording_credits),
        work_usages=(RecordingWorkUsage.create(uuid7(), work_id, RecordingWorkUsageKind.COMPLETE),),
    )


def _published_person(person_id: UUID) -> Person:
    return Person.create(
        person_id,
        PersonContent.create("Performer"),
        editorial_status=PersonEditorialStatus.PUBLISHED,
    )


@pytest.mark.asyncio
async def test_recording_service_publishes_with_locked_published_work() -> None:
    work = MusicalWork.create(
        uuid7(),
        WorkContent.create("Work", provenance="Editorial note"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    recordings: dict[UUID, Recording] = {}
    work_records = {work.id: work}
    person = _published_person(uuid7())
    uow = FakeMusicCatalogUnitOfWork({}, works=work_records, recordings=recordings)
    service = RecordingService(pair_scope(lambda: uow, lambda: FakePeopleCatalogUnitOfWork({person.id: person})))

    recording = await service.create(_content(work.id, person.id, additional_target_id=uuid7()))
    published = await service.publish(recording.id)

    assert published.editorial_status is EditorialStatus.PUBLISHED
    assert isinstance(uow.recordings, FakeRecordingRepository)
    assert uow.recordings.locked_ids == [recording.id]
    assert isinstance(uow.works, FakeMusicalWorkRepository)
    assert uow.works.locked_ids == [work.id]

    draft_work = MusicalWork.create(uuid7(), WorkContent.create("Draft", provenance="Editorial note"))
    work_records[draft_work.id] = draft_work
    with pytest.raises(RecordingWorkNotPublished):
        await service.replace_content(recording.id, _content(draft_work.id, person.id))
    assert recordings[recording.id] == published
    with pytest.raises(RecordingPrimaryTargetNotPublished):
        await service.replace_content(recording.id, _content(work.id, uuid7()))
    assert recordings[recording.id] == published


@pytest.mark.asyncio
async def test_recording_service_rejects_unpublished_work() -> None:
    work = MusicalWork.create(uuid7(), WorkContent.create("Draft", provenance="Editorial note"))
    recordings: dict[UUID, Recording] = {}
    person = _published_person(uuid7())
    service = RecordingService(
        pair_scope(
            lambda: FakeMusicCatalogUnitOfWork({}, works={work.id: work}, recordings=recordings),
            lambda: FakePeopleCatalogUnitOfWork({person.id: person}),
        )
    )
    recording = await service.create(_content(work.id, person.id))

    with pytest.raises(RecordingWorkNotPublished):
        await service.publish(recording.id)

    assert recordings[recording.id].editorial_status is EditorialStatus.DRAFT


@pytest.mark.asyncio
async def test_recording_service_requires_published_primary_target() -> None:
    work = MusicalWork.create(
        uuid7(),
        WorkContent.create("Work", provenance="Editorial note"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    draft_person = Person.create(uuid7(), PersonContent.create("Draft performer"))
    recordings: dict[UUID, Recording] = {}
    service = RecordingService(
        pair_scope(
            lambda: FakeMusicCatalogUnitOfWork({}, works={work.id: work}, recordings=recordings),
            lambda: FakePeopleCatalogUnitOfWork({draft_person.id: draft_person}),
        )
    )
    recording = await service.create(_content(work.id, draft_person.id))

    with pytest.raises(RecordingPrimaryTargetNotPublished):
        await service.publish(recording.id)


@pytest.mark.asyncio
async def test_recording_service_rejects_unpublished_group_target() -> None:
    work = MusicalWork.create(
        uuid7(),
        WorkContent.create("Work", provenance="Editorial note"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    draft_group = Group.create(uuid7(), GroupContent.create("Draft group"))
    recordings: dict[UUID, Recording] = {}
    service = RecordingService(
        pair_scope(
            lambda: FakeMusicCatalogUnitOfWork(
                {}, works={work.id: work}, groups={draft_group.id: draft_group}, recordings=recordings
            ),
            lambda: FakePeopleCatalogUnitOfWork({}),
        )
    )
    recording = await service.create(_content(work.id, draft_group.id, target_kind=RecordingCreditTargetKind.GROUP))

    with pytest.raises(RecordingPrimaryTargetNotPublished):
        await service.publish(recording.id)


@pytest.mark.asyncio
async def test_one_published_primary_target_is_enough() -> None:
    work = MusicalWork.create(
        uuid7(),
        WorkContent.create("Work", provenance="Editorial note"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    person = _published_person(uuid7())
    draft_group = Group.create(uuid7(), GroupContent.create("Draft group"))
    content = RecordingContent.create(
        "Take",
        recording_credits=(
            RecordingCredit.create(uuid7(), RecordingCreditTargetKind.GROUP, draft_group.id, BillingRole.PRIMARY),
            RecordingCredit.create(uuid7(), RecordingCreditTargetKind.PERSON, person.id, BillingRole.PRIMARY),
        ),
        work_usages=(RecordingWorkUsage.create(uuid7(), work.id, RecordingWorkUsageKind.COMPLETE),),
    )
    recordings: dict[UUID, Recording] = {}
    service = RecordingService(
        pair_scope(
            lambda: FakeMusicCatalogUnitOfWork(
                {}, works={work.id: work}, groups={draft_group.id: draft_group}, recordings=recordings
            ),
            lambda: FakePeopleCatalogUnitOfWork({person.id: person}),
        )
    )

    recording = await service.create(content)
    assert (await service.publish(recording.id)).editorial_status is EditorialStatus.PUBLISHED
