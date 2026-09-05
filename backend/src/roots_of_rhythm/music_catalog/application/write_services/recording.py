from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.music_catalog.application.errors import (
    RecordingConflict,
    RecordingLyricsVersionNotPerformable,
    RecordingLyricsVersionNotPublished,
    RecordingLyricsVersionWorkMismatch,
    RecordingNotFound,
    RecordingPrimaryTargetNotPublished,
    RecordingWorkNotPublished,
    UniqueConstraintViolation,
)
from roots_of_rhythm.music_catalog.application.ports import (
    GroupRepository,
    LyricsVersionRepository,
    MusicalWorkRepository,
    RecordingRepository,
)
from roots_of_rhythm.people_catalog.application.ports import PersonRepository

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import (
        Recording,
        RecordingContent,
    )

type RecordingRepositoryFactory = Callable[[Transaction], RecordingRepository]
type MusicalWorkRepositoryFactory = Callable[[Transaction], MusicalWorkRepository]
type LyricsVersionRepositoryFactory = Callable[[Transaction], LyricsVersionRepository]
type GroupRepositoryFactory = Callable[[Transaction], GroupRepository]
type PersonRepositoryFactory = Callable[[Transaction], PersonRepository]


class PublishRecording:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        recording_repository_factory: RecordingRepositoryFactory,
        work_repository_factory: MusicalWorkRepositoryFactory,
        lyrics_version_repository_factory: LyricsVersionRepositoryFactory,
        group_repository_factory: GroupRepositoryFactory,
        person_repository_factory: PersonRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._recording_repository_factory = recording_repository_factory
        self._work_repository_factory = work_repository_factory
        self._lyrics_version_repository_factory = lyrics_version_repository_factory
        self._group_repository_factory = group_repository_factory
        self._person_repository_factory = person_repository_factory

    async def execute(self, recording_id: UUID) -> Recording:
        async with self._transaction_scope() as transaction:
            recording_repository = self._recording_repository_factory(transaction)
            recording = await recording_repository.get(recording_id, for_update=True)
            if recording is None:
                raise RecordingNotFound(str(recording_id))

            published = recording.publish()
            await _validate_publication(
                published,
                self._work_repository_factory(transaction),
                self._group_repository_factory(transaction),
                self._person_repository_factory(transaction),
                self._lyrics_version_repository_factory(transaction),
            )

            try:
                await recording_repository.save_status(published)
            except LookupError as error:
                raise RecordingNotFound(str(published.id)) from error

            await transaction.commit()
            return published


class ReplaceRecordingContent:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        recording_repository_factory: RecordingRepositoryFactory,
        work_repository_factory: MusicalWorkRepositoryFactory,
        lyrics_version_repository_factory: LyricsVersionRepositoryFactory,
        group_repository_factory: GroupRepositoryFactory,
        person_repository_factory: PersonRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._recording_repository_factory = recording_repository_factory
        self._work_repository_factory = work_repository_factory
        self._lyrics_version_repository_factory = lyrics_version_repository_factory
        self._group_repository_factory = group_repository_factory
        self._person_repository_factory = person_repository_factory

    async def execute(self, recording_id: UUID, content: RecordingContent) -> Recording:
        async with self._transaction_scope() as transaction:
            recording_repository = self._recording_repository_factory(transaction)
            recording = await recording_repository.get(recording_id, for_update=True)
            if recording is None:
                raise RecordingNotFound(str(recording_id))

            updated = recording.replace_content(content)
            if updated.is_published:
                await _validate_publication(
                    updated,
                    self._work_repository_factory(transaction),
                    self._group_repository_factory(transaction),
                    self._person_repository_factory(transaction),
                    self._lyrics_version_repository_factory(transaction),
                )

            try:
                await recording_repository.save(updated)
            except LookupError as error:
                raise RecordingNotFound(str(recording_id)) from error
            except UniqueConstraintViolation as error:
                raise RecordingConflict from error

            await transaction.commit()
            return updated


async def _validate_publication(
    recording: Recording,
    work_repository: MusicalWorkRepository,
    group_repository: GroupRepository,
    person_repository: PersonRepository,
    lyrics_version_repository: LyricsVersionRepository,
) -> None:
    work_ids = {usage.work_id for usage in recording.work_usages}
    published_works = await work_repository.get_published_by_ids(work_ids, for_update=True)
    if not published_works:
        raise RecordingWorkNotPublished(str(recording.id))

    group_ids = {
        credit.target_id for credit in recording.credits if credit.is_primary_billing and credit.is_group_target
    }
    published_groups = await group_repository.get_published_by_ids(group_ids, for_update=True)
    if not published_groups:
        person_ids = {
            credit.target_id for credit in recording.credits if credit.is_primary_billing and credit.is_person_target
        }
        published_people = await person_repository.get_published_by_ids(person_ids, for_update=True)
        if not published_people:
            raise RecordingPrimaryTargetNotPublished(str(recording.id))

    lyrics_version_ids = {usage.lyrics_version_id for usage in recording.lyrics_usages}
    published_lyrics = await lyrics_version_repository.get_published_by_ids(
        lyrics_version_ids,
        for_update=True,
    )
    for usage in recording.lyrics_usages:
        version = published_lyrics.get(usage.lyrics_version_id)
        if version is None:
            raise RecordingLyricsVersionNotPublished(str(usage.lyrics_version_id))
        if not version.is_performable or version.is_machine_translated:
            raise RecordingLyricsVersionNotPerformable(str(version.id))
        if version.work_id not in work_ids:
            raise RecordingLyricsVersionWorkMismatch(str(version.id))
