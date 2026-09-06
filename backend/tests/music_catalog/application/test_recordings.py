from types import SimpleNamespace
from uuid import UUID, uuid7

import pytest
from tests.music_catalog.fakes.groups import FakeGroupRepository
from tests.music_catalog.fakes.lyrics import FakeLyricsVersionRepository
from tests.music_catalog.fakes.recordings import FakeRecordingRepository
from tests.music_catalog.fakes.works import FakeMusicalWorkRepository
from tests.people_catalog.fakes.persons import FakePersonRepository
from tests.support.scopes import counting_transaction_scope

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
    *,
    recordings: dict[UUID, Recording] | None = None,
    works: dict[UUID, MusicalWork] | None = None,
    lyrics_versions: dict[UUID, LyricsVersion] | None = None,
    groups: dict[UUID, Group] | None = None,
    persons: dict[UUID, Person] | None = None,
) -> tuple[RecordingService, PublishRecording, ReplaceRecordingContent, SimpleNamespace, SimpleNamespace]:
    scope, _counting = counting_transaction_scope()
    music = SimpleNamespace(
        recordings=FakeRecordingRepository(recordings if recordings is not None else {}),
        works=FakeMusicalWorkRepository(works if works is not None else {}),
        lyrics_versions=FakeLyricsVersionRepository(lyrics_versions if lyrics_versions is not None else {}),
        groups=FakeGroupRepository(groups if groups is not None else {}),
    )
    people = SimpleNamespace(persons=FakePersonRepository(persons if persons is not None else {}))

    service = RecordingService(scope, lambda _transaction: music.recordings)
    publish = PublishRecording(
        transaction_scope=scope,
        recording_repository_factory=lambda _transaction: music.recordings,
        work_repository_factory=lambda _transaction: music.works,
        lyrics_version_repository_factory=lambda _transaction: music.lyrics_versions,
        group_repository_factory=lambda _transaction: music.groups,
        person_repository_factory=lambda _transaction: people.persons,
    )
    replace = ReplaceRecordingContent(
        transaction_scope=scope,
        recording_repository_factory=lambda _transaction: music.recordings,
        work_repository_factory=lambda _transaction: music.works,
        lyrics_version_repository_factory=lambda _transaction: music.lyrics_versions,
        group_repository_factory=lambda _transaction: music.groups,
        person_repository_factory=lambda _transaction: people.persons,
    )
    return service, publish, replace, music, people


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
    service, publish_recording, replace_recording_content, music, _people = _operations(
        recordings=recordings, works=work_records, persons={person.id: person}
    )

    recording = await service.create(_content(work.id, person.id, additional_target_id=uuid7()))
    published = await publish_recording.execute(recording.id)

    assert published.is_published
    assert music.recordings.locked_ids == [recording.id]
    assert music.works.locked_ids == [work.id]

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
    service, publish_recording, _replace_recording_content, _music, _people = _operations(
        recordings=recordings, works={work.id: work}, persons={person.id: person}
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
    service, publish_recording, _replace_recording_content, _music, _people = _operations(
        recordings=recordings, works={work.id: work}, persons={draft_person.id: draft_person}
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
    service, publish_recording, _replace_recording_content, _music, _people = _operations(
        recordings=recordings, works={work.id: work}, groups={draft_group.id: draft_group}
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
    service, publish_recording, _replace_recording_content, music, people = _operations(
        recordings=recordings,
        works={work.id: work},
        groups={draft_group.id: draft_group},
        persons={person.id: person},
    )

    recording = await service.create(content)
    assert (await publish_recording.execute(recording.id)).is_published
    assert music.groups.batch_calls == [(draft_group.id,)]
    assert music.groups.locked_ids == [draft_group.id]
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
    service, publish_recording, _replace_recording_content, _music, _people = _operations(
        recordings=recordings, works={work.id: work}, lyrics_versions=versions, persons={person.id: person}
    )

    recording = await service.create(_content(work.id, person.id, lyrics_version_id=valid.id))
    await publish_recording.execute(recording.id)

    for invalid, error in invalid_cases:
        draft = await service.create(_content(work.id, person.id, lyrics_version_id=invalid.id))
        with pytest.raises(error):
            await publish_recording.execute(draft.id)


@pytest.mark.asyncio
async def test_draft_replace_does_not_read_publication_dependencies() -> None:
    service, _publish_recording, replace_recording_content, music, _people = _operations()
    draft = await service.create(RecordingContent.create("Draft"))

    updated = await replace_recording_content.execute(draft.id, RecordingContent.create("Changed"))

    assert updated.title == "Changed"
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
    service, publish_recording, _replace_recording_content, music, _people = _operations(
        works={work.id: work for work in works},
        lyrics_versions={version.id: version for version in versions},
        persons={person.id: person},
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
    assert music.works.batch_calls == [work_ids]
    assert music.works.locked_ids == list(work_ids)
    assert music.lyrics_versions.batch_calls == [version_ids]
    assert music.lyrics_versions.locked_ids == list(version_ids)


@pytest.mark.asyncio
async def test_create_maps_repository_unique_constraint_to_recording_conflict() -> None:
    class ConflictingRecordingRepository(FakeRecordingRepository):
        async def add(self, recording: Recording) -> None:
            raise UniqueConstraintViolation("recording constraint")

    service, _publish_recording, _replace_recording_content, music, _people = _operations(recordings={})
    music.recordings = ConflictingRecordingRepository({})

    with pytest.raises(RecordingConflict):
        await service.create(RecordingContent.create("Draft"))


@pytest.mark.asyncio
async def test_replace_maps_repository_unique_constraint_to_recording_conflict() -> None:
    class ConflictingRecordingRepository(FakeRecordingRepository):
        async def save(self, recording: Recording) -> None:
            raise UniqueConstraintViolation("recording constraint")

    service, _publish_recording, replace_recording_content, music, _people = _operations(recordings={})
    music.recordings = ConflictingRecordingRepository({})
    draft = await service.create(RecordingContent.create("Draft"))

    with pytest.raises(RecordingConflict):
        await replace_recording_content.execute(draft.id, RecordingContent.create("Changed"))
