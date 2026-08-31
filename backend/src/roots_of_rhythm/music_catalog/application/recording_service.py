from collections.abc import Callable
from uuid import UUID, uuid7

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.music_catalog.application.errors import (
    RecordingLyricsVersionNotPerformable,
    RecordingLyricsVersionNotPublished,
    RecordingLyricsVersionWorkMismatch,
    RecordingNotFound,
    RecordingPrimaryTargetNotPublished,
    RecordingWorkNotPublished,
)
from roots_of_rhythm.music_catalog.application.ports import (
    GroupRepository,
    LyricsVersionRepository,
    MusicalWorkRepository,
    RecordingRepository,
)
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    EditorialStatus,
    LyricsCreationMethod,
    LyricsUsageKind,
    Recording,
    RecordingContent,
    RecordingCreditTargetKind,
)
from roots_of_rhythm.people_catalog.application.ports import PersonRepository

type RecordingRepositoryFactory = Callable[[Transaction], RecordingRepository]
type MusicalWorkRepositoryFactory = Callable[[Transaction], MusicalWorkRepository]
type LyricsVersionRepositoryFactory = Callable[[Transaction], LyricsVersionRepository]
type GroupRepositoryFactory = Callable[[Transaction], GroupRepository]
type PersonRepositoryFactory = Callable[[Transaction], PersonRepository]


class RecordingService:
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

    async def create(self, content: RecordingContent, *, recording_id: UUID | None = None) -> Recording:
        async with self._transaction_scope() as transaction:
            recording = Recording.create(recording_id or uuid7(), content)
            repository = self._recording_repository_factory(transaction)
            await repository.add(recording)
            await transaction.commit()
            return recording

    async def replace_content(self, recording_id: UUID, content: RecordingContent) -> Recording:
        async with self._transaction_scope() as transaction:
            recording_repository = self._recording_repository_factory(transaction)
            work_repository = self._work_repository_factory(transaction)
            lyrics_version_repository = self._lyrics_version_repository_factory(transaction)
            group_repository = self._group_repository_factory(transaction)
            person_repository = self._person_repository_factory(transaction)
            recording = await self._get(recording_repository, recording_id, for_update=True)
            updated = recording.replace_content(content)
            if updated.editorial_status is EditorialStatus.PUBLISHED and not await self._has_published_work(
                work_repository, updated
            ):
                raise RecordingWorkNotPublished(str(recording_id))
            if updated.editorial_status is EditorialStatus.PUBLISHED and not await self._has_published_primary_target(
                group_repository, person_repository, updated
            ):
                raise RecordingPrimaryTargetNotPublished(str(recording_id))
            if updated.editorial_status is EditorialStatus.PUBLISHED:
                await self._validate_lyrics_usages(lyrics_version_repository, updated)
            await self._save(recording_repository, updated)
            await transaction.commit()
            return updated

    async def publish(self, recording_id: UUID) -> Recording:
        async with self._transaction_scope() as transaction:
            recording_repository = self._recording_repository_factory(transaction)
            recording = await self._get(recording_repository, recording_id, for_update=True)
            updated = recording.publish()
            if not await self._has_published_work(self._work_repository_factory(transaction), updated):
                raise RecordingWorkNotPublished(str(recording_id))
            if not await self._has_published_primary_target(
                self._group_repository_factory(transaction), self._person_repository_factory(transaction), updated
            ):
                raise RecordingPrimaryTargetNotPublished(str(recording_id))
            await self._validate_lyrics_usages(self._lyrics_version_repository_factory(transaction), updated)
            await self._save_status(recording_repository, updated)
            await transaction.commit()
            return updated

    async def archive(self, recording_id: UUID) -> Recording:
        async with self._transaction_scope() as transaction:
            recording_repository = self._recording_repository_factory(transaction)
            recording = await self._get(recording_repository, recording_id, for_update=True)
            updated = recording.archive()
            await self._save_status(recording_repository, updated)
            await transaction.commit()
            return updated

    @staticmethod
    async def _get(
        recordings: RecordingRepository,
        recording_id: UUID,
        *,
        for_update: bool = False,
    ) -> Recording:
        recording = await recordings.get(recording_id, for_update=for_update)
        if recording is None:
            raise RecordingNotFound(str(recording_id))
        return recording

    @staticmethod
    async def _save(recordings: RecordingRepository, recording: Recording) -> None:
        try:
            await recordings.save(recording)
        except LookupError as error:
            raise RecordingNotFound(str(recording.id)) from error

    @staticmethod
    async def _save_status(recordings: RecordingRepository, recording: Recording) -> None:
        try:
            await recordings.save_status(recording)
        except LookupError as error:
            raise RecordingNotFound(str(recording.id)) from error

    @staticmethod
    async def _has_published_work(works: MusicalWorkRepository, recording: Recording) -> bool:
        for work_id in sorted({usage.work_id for usage in recording.work_usages}):
            if await works.get_published(work_id, for_update=True) is not None:
                return True
        return False

    @staticmethod
    async def _validate_lyrics_usages(lyrics_versions: LyricsVersionRepository, recording: Recording) -> None:
        work_ids = {usage.work_id for usage in recording.work_usages}
        for usage in sorted(recording.lyrics_usages, key=lambda item: item.lyrics_version_id):
            version = await lyrics_versions.get_published(usage.lyrics_version_id, for_update=True)
            if version is None:
                raise RecordingLyricsVersionNotPublished(str(usage.lyrics_version_id))
            if (
                version.usage_kind is not LyricsUsageKind.PERFORMABLE
                or version.creation_method is LyricsCreationMethod.MACHINE_TRANSLATION
            ):
                raise RecordingLyricsVersionNotPerformable(str(version.id))
            if version.work_id not in work_ids:
                raise RecordingLyricsVersionWorkMismatch(str(version.id))

    @staticmethod
    async def _has_published_primary_target(
        groups: GroupRepository,
        persons: PersonRepository,
        recording: Recording,
    ) -> bool:
        primary_credits = sorted(
            (credit for credit in recording.credits if credit.billing_role is BillingRole.PRIMARY),
            key=lambda credit: (credit.target_kind.value, credit.target_id),
        )
        for credit in primary_credits:
            match credit.target_kind:
                case RecordingCreditTargetKind.PERSON:
                    if await persons.get_published(credit.target_id, for_update=True) is not None:
                        return True
                case RecordingCreditTargetKind.GROUP:
                    if await groups.get_published(credit.target_id, for_update=True) is not None:
                        return True
        return False
