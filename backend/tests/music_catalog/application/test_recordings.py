from uuid import UUID, uuid7

import pytest
from tests.music_catalog.fakes import (
    FakeGroupRepository,
    FakeLyricsVersionRepository,
    FakeMusicalWorkRepository,
    FakeMusicCatalogUnitOfWork,
    FakeRecordingRepository,
)
from tests.people_catalog.fakes import FakePeopleCatalogUnitOfWork, FakePersonRepository

from roots_of_rhythm.music_catalog.application import (
    PublishRecording,
    RecordingConflict,
    RecordingLyricsVersionNotPerformable,
    RecordingLyricsVersionNotPublished,
    RecordingLyricsVersionWorkMismatch,
    RecordingPrimaryTargetNotPublished,
    RecordingService,
    RecordingWorkNotPublished,
    ReplaceRecordingContent,
    UniqueConstraintViolation,
)
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    EditorialStatus,
    Group,
    GroupContent,
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersion,
    LyricsVersionContent,
    MusicalWork,
    Recording,
    RecordingContent,
    RecordingCredit,
    RecordingCreditTargetKind,
    RecordingLyricsUsage,
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
    lyrics_version_id: UUID | None = None,
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
        lyrics_usages=(
            (RecordingLyricsUsage.create(uuid7(), lyrics_version_id),) if lyrics_version_id is not None else ()
        ),
    )


def _published_person(person_id: UUID) -> Person:
    return Person.create(
        person_id,
        PersonContent.create("Performer"),
        editorial_status=PersonEditorialStatus.PUBLISHED,
    )


def _operations(
    music: FakeMusicCatalogUnitOfWork,
    people: FakePeopleCatalogUnitOfWork,
) -> tuple[RecordingService, PublishRecording, ReplaceRecordingContent]:
    service = RecordingService(
        transaction_scope=lambda: music,
        recording_repository_factory=lambda _transaction: music.recordings,
    )
    publish = PublishRecording(
        transaction_scope=lambda: music,
        recording_repository_factory=lambda _transaction: music.recordings,
        work_repository_factory=lambda _transaction: music.works,
        lyrics_version_repository_factory=lambda _transaction: music.lyrics_versions,
        group_repository_factory=lambda _transaction: music.groups,
        person_repository_factory=lambda _transaction: people.persons,
    )
    replace = ReplaceRecordingContent(
        transaction_scope=lambda: music,
        recording_repository_factory=lambda _transaction: music.recordings,
        work_repository_factory=lambda _transaction: music.works,
        lyrics_version_repository_factory=lambda _transaction: music.lyrics_versions,
        group_repository_factory=lambda _transaction: music.groups,
        person_repository_factory=lambda _transaction: people.persons,
    )
    return service, publish, replace


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
    service, publish_recording, replace_recording_content = _operations(
        uow, FakePeopleCatalogUnitOfWork({person.id: person})
    )

    recording = await service.create(_content(work.id, person.id, additional_target_id=uuid7()))
    published = await publish_recording.execute(recording.id)

    assert published.is_published
    assert isinstance(uow.recordings, FakeRecordingRepository)
    assert uow.recordings.locked_ids == [recording.id]
    assert isinstance(uow.works, FakeMusicalWorkRepository)
    assert uow.works.locked_ids == [work.id]

    draft_work = MusicalWork.create(uuid7(), WorkContent.create("Draft", provenance="Editorial note"))
    work_records[draft_work.id] = draft_work
    with pytest.raises(RecordingWorkNotPublished):
        await replace_recording_content.execute(recording.id, _content(draft_work.id, person.id))
    assert recordings[recording.id] == published
    with pytest.raises(RecordingPrimaryTargetNotPublished):
        await replace_recording_content.execute(recording.id, _content(work.id, uuid7()))
    assert recordings[recording.id] == published


@pytest.mark.asyncio
async def test_recording_service_rejects_unpublished_work() -> None:
    work = MusicalWork.create(uuid7(), WorkContent.create("Draft", provenance="Editorial note"))
    recordings: dict[UUID, Recording] = {}
    person = _published_person(uuid7())
    service, publish_recording, _replace_recording_content = _operations(
        FakeMusicCatalogUnitOfWork({}, works={work.id: work}, recordings=recordings),
        FakePeopleCatalogUnitOfWork({person.id: person}),
    )
    recording = await service.create(_content(work.id, person.id))

    with pytest.raises(RecordingWorkNotPublished):
        await publish_recording.execute(recording.id)

    assert recordings[recording.id].is_draft


@pytest.mark.asyncio
async def test_recording_service_requires_published_primary_target() -> None:
    work = MusicalWork.create(
        uuid7(),
        WorkContent.create("Work", provenance="Editorial note"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    draft_person = Person.create(uuid7(), PersonContent.create("Draft performer"))
    recordings: dict[UUID, Recording] = {}
    service, publish_recording, _replace_recording_content = _operations(
        FakeMusicCatalogUnitOfWork({}, works={work.id: work}, recordings=recordings),
        FakePeopleCatalogUnitOfWork({draft_person.id: draft_person}),
    )
    recording = await service.create(_content(work.id, draft_person.id))

    with pytest.raises(RecordingPrimaryTargetNotPublished):
        await publish_recording.execute(recording.id)


@pytest.mark.asyncio
async def test_recording_service_rejects_unpublished_group_target() -> None:
    work = MusicalWork.create(
        uuid7(),
        WorkContent.create("Work", provenance="Editorial note"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    draft_group = Group.create(uuid7(), GroupContent.create("Draft group"))
    recordings: dict[UUID, Recording] = {}
    service, publish_recording, _replace_recording_content = _operations(
        FakeMusicCatalogUnitOfWork(
            {}, works={work.id: work}, groups={draft_group.id: draft_group}, recordings=recordings
        ),
        FakePeopleCatalogUnitOfWork({}),
    )
    recording = await service.create(_content(work.id, draft_group.id, target_kind=RecordingCreditTargetKind.GROUP))

    with pytest.raises(RecordingPrimaryTargetNotPublished):
        await publish_recording.execute(recording.id)


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
    music = FakeMusicCatalogUnitOfWork(
        {}, works={work.id: work}, groups={draft_group.id: draft_group}, recordings=recordings
    )
    people = FakePeopleCatalogUnitOfWork({person.id: person})
    service, publish_recording, _replace_recording_content = _operations(music, people)

    recording = await service.create(content)
    assert (await publish_recording.execute(recording.id)).is_published
    assert isinstance(music.groups, FakeGroupRepository)
    assert music.groups.batch_calls == [(draft_group.id,)]
    assert music.groups.locked_ids == [draft_group.id]
    assert isinstance(people.persons, FakePersonRepository)
    assert people.persons.batch_calls == [(person.id,)]
    assert people.persons.locked_ids == [person.id]


@pytest.mark.asyncio
async def test_recording_service_validates_lyrics_usages() -> None:
    work = MusicalWork.create(
        uuid7(),
        WorkContent.create("Work", provenance="Editorial note"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    person = _published_person(uuid7())

    def version(
        *,
        work_id: UUID = work.id,
        usage_kind: LyricsUsageKind = LyricsUsageKind.PERFORMABLE,
        status: EditorialStatus = EditorialStatus.PUBLISHED,
    ) -> LyricsVersion:
        return LyricsVersion.create(
            uuid7(),
            work_id,
            uuid7(),
            LyricsVersionContent.create(
                language_tag="en",
                usage_kind=usage_kind,
                creation_method=(
                    LyricsCreationMethod.HUMAN_TRANSLATION
                    if usage_kind is LyricsUsageKind.READING_TRANSLATION
                    else LyricsCreationMethod.ORIGINAL
                ),
            ),
            editorial_status=status,
        )

    valid = version()
    invalid_cases = (
        (version(status=EditorialStatus.DRAFT), RecordingLyricsVersionNotPublished),
        (version(usage_kind=LyricsUsageKind.READING_TRANSLATION), RecordingLyricsVersionNotPerformable),
        (version(work_id=uuid7()), RecordingLyricsVersionWorkMismatch),
    )
    versions = {item.id: item for item, _error in invalid_cases} | {valid.id: valid}
    recordings: dict[UUID, Recording] = {}
    service, publish_recording, _replace_recording_content = _operations(
        FakeMusicCatalogUnitOfWork({}, works={work.id: work}, lyrics_versions=versions, recordings=recordings),
        FakePeopleCatalogUnitOfWork({person.id: person}),
    )

    recording = await service.create(_content(work.id, person.id, lyrics_version_id=valid.id))
    await publish_recording.execute(recording.id)

    for invalid, error in invalid_cases:
        draft = await service.create(_content(work.id, person.id, lyrics_version_id=invalid.id))
        with pytest.raises(error):
            await publish_recording.execute(draft.id)


@pytest.mark.asyncio
async def test_draft_replace_does_not_read_publication_dependencies() -> None:
    music = FakeMusicCatalogUnitOfWork({})
    service, _publish_recording, replace_recording_content = _operations(music, FakePeopleCatalogUnitOfWork({}))
    draft = await service.create(RecordingContent.create("Draft"))

    updated = await replace_recording_content.execute(draft.id, RecordingContent.create("Changed"))

    assert updated.title == "Changed"
    assert isinstance(music.works, FakeMusicalWorkRepository)
    assert isinstance(music.groups, FakeGroupRepository)
    assert isinstance(music.lyrics_versions, FakeLyricsVersionRepository)
    assert music.works.batch_calls == []
    assert music.groups.batch_calls == []
    assert music.lyrics_versions.batch_calls == []


@pytest.mark.asyncio
async def test_publish_batches_medley_works_and_lyrics_with_write_locks() -> None:
    works = tuple(
        MusicalWork.create(
            uuid7(),
            WorkContent.create(f"Work {position}", provenance="Editorial note"),
            editorial_status=EditorialStatus.PUBLISHED,
        )
        for position in (1, 2)
    )
    versions = tuple(
        LyricsVersion.create(
            uuid7(),
            work.id,
            uuid7(),
            LyricsVersionContent.create(
                language_tag="en",
                usage_kind=LyricsUsageKind.PERFORMABLE,
                creation_method=LyricsCreationMethod.ORIGINAL,
            ),
            editorial_status=EditorialStatus.PUBLISHED,
        )
        for work in works
    )
    person = _published_person(uuid7())
    music = FakeMusicCatalogUnitOfWork(
        {},
        works={work.id: work for work in works},
        lyrics_versions={version.id: version for version in versions},
    )
    service, publish_recording, _replace_recording_content = _operations(
        music, FakePeopleCatalogUnitOfWork({person.id: person})
    )
    recording = await service.create(
        RecordingContent.create(
            "Medley",
            recording_credits=(
                RecordingCredit.create(uuid7(), RecordingCreditTargetKind.PERSON, person.id, BillingRole.PRIMARY),
            ),
            work_usages=tuple(
                RecordingWorkUsage.create(uuid7(), work.id, RecordingWorkUsageKind.MEDLEY_COMPONENT, position=position)
                for position, work in enumerate(works, start=1)
            ),
            lyrics_usages=tuple(RecordingLyricsUsage.create(uuid7(), version.id) for version in versions),
        )
    )

    await publish_recording.execute(recording.id)

    work_ids = tuple(sorted(work.id for work in works))
    version_ids = tuple(sorted(version.id for version in versions))
    assert isinstance(music.works, FakeMusicalWorkRepository)
    assert isinstance(music.lyrics_versions, FakeLyricsVersionRepository)
    assert music.works.batch_calls == [work_ids]
    assert music.works.locked_ids == list(work_ids)
    assert music.lyrics_versions.batch_calls == [version_ids]
    assert music.lyrics_versions.locked_ids == list(version_ids)


@pytest.mark.asyncio
async def test_create_maps_repository_unique_constraint_to_recording_conflict() -> None:
    class ConflictingRecordingRepository(FakeRecordingRepository):
        async def add(self, recording: Recording) -> None:
            raise UniqueConstraintViolation("recording constraint")

    music = FakeMusicCatalogUnitOfWork({})
    music.recordings = ConflictingRecordingRepository({})
    service, _publish_recording, _replace_recording_content = _operations(music, FakePeopleCatalogUnitOfWork({}))

    with pytest.raises(RecordingConflict):
        await service.create(RecordingContent.create("Draft"))


@pytest.mark.asyncio
async def test_replace_maps_repository_unique_constraint_to_recording_conflict() -> None:
    class ConflictingRecordingRepository(FakeRecordingRepository):
        async def save(self, recording: Recording) -> None:
            raise UniqueConstraintViolation("recording constraint")

    music = FakeMusicCatalogUnitOfWork({})
    music.recordings = ConflictingRecordingRepository({})
    service, _publish_recording, replace_recording_content = _operations(music, FakePeopleCatalogUnitOfWork({}))
    draft = await service.create(RecordingContent.create("Draft"))

    with pytest.raises(RecordingConflict):
        await replace_recording_content.execute(draft.id, RecordingContent.create("Changed"))
