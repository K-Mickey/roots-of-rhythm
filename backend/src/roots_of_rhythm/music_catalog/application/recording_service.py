from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from uuid import UUID, uuid7

from roots_of_rhythm.music_catalog.application.errors import (
    RecordingLyricsVersionNotPerformable,
    RecordingLyricsVersionNotPublished,
    RecordingLyricsVersionWorkMismatch,
    RecordingNotFound,
    RecordingPrimaryTargetNotPublished,
    RecordingWorkNotPublished,
)
from roots_of_rhythm.music_catalog.application.ports import RecordingUnitOfWork
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    EditorialStatus,
    LyricsCreationMethod,
    LyricsUsageKind,
    Recording,
    RecordingContent,
    RecordingCreditTargetKind,
)
from roots_of_rhythm.people_catalog.application.ports import PeopleCatalogUnitOfWork

type MusicPeopleScopeFactory = Callable[
    [],
    AbstractAsyncContextManager[tuple[RecordingUnitOfWork, PeopleCatalogUnitOfWork]],
]


class RecordingService:
    def __init__(self, catalogs: MusicPeopleScopeFactory) -> None:
        self._catalogs = catalogs

    async def create(self, content: RecordingContent, *, recording_id: UUID | None = None) -> Recording:
        async with self._catalogs() as (uow, _people):
            recording = Recording.create(recording_id or uuid7(), content)
            await uow.recordings.add(recording)
            await uow.commit()
            return recording

    async def replace_content(self, recording_id: UUID, content: RecordingContent) -> Recording:
        async with self._catalogs() as (uow, people):
            recording = await self._get(uow, recording_id, for_update=True)
            updated = recording.replace_content(content)
            if updated.editorial_status is EditorialStatus.PUBLISHED and not await self._has_published_work(
                uow, updated
            ):
                raise RecordingWorkNotPublished(str(recording_id))
            if updated.editorial_status is EditorialStatus.PUBLISHED and not await self._has_published_primary_target(
                uow, people, updated
            ):
                raise RecordingPrimaryTargetNotPublished(str(recording_id))
            if updated.editorial_status is EditorialStatus.PUBLISHED:
                await self._validate_lyrics_usages(uow, updated)
            await self._save(uow, updated)
            await uow.commit()
            return updated

    async def publish(self, recording_id: UUID) -> Recording:
        async with self._catalogs() as (uow, people):
            recording = await self._get(uow, recording_id, for_update=True)
            updated = recording.publish()
            if not await self._has_published_work(uow, updated):
                raise RecordingWorkNotPublished(str(recording_id))
            if not await self._has_published_primary_target(uow, people, updated):
                raise RecordingPrimaryTargetNotPublished(str(recording_id))
            await self._validate_lyrics_usages(uow, updated)
            await self._save_status(uow, updated)
            await uow.commit()
            return updated

    async def archive(self, recording_id: UUID) -> Recording:
        async with self._catalogs() as (uow, _people):
            recording = await self._get(uow, recording_id, for_update=True)
            updated = recording.archive()
            await self._save_status(uow, updated)
            await uow.commit()
            return updated

    @staticmethod
    async def _get(
        uow: RecordingUnitOfWork,
        recording_id: UUID,
        *,
        for_update: bool = False,
    ) -> Recording:
        recording = await uow.recordings.get(recording_id, for_update=for_update)
        if recording is None:
            raise RecordingNotFound(str(recording_id))
        return recording

    @staticmethod
    async def _save(uow: RecordingUnitOfWork, recording: Recording) -> None:
        try:
            await uow.recordings.save(recording)
        except LookupError as error:
            raise RecordingNotFound(str(recording.id)) from error

    @staticmethod
    async def _save_status(uow: RecordingUnitOfWork, recording: Recording) -> None:
        try:
            await uow.recordings.save_status(recording)
        except LookupError as error:
            raise RecordingNotFound(str(recording.id)) from error

    @staticmethod
    async def _has_published_work(uow: RecordingUnitOfWork, recording: Recording) -> bool:
        for work_id in sorted({usage.work_id for usage in recording.work_usages}):
            if await uow.works.get_published(work_id, for_update=True) is not None:
                return True
        return False

    @staticmethod
    async def _validate_lyrics_usages(uow: RecordingUnitOfWork, recording: Recording) -> None:
        work_ids = {usage.work_id for usage in recording.work_usages}
        for usage in sorted(recording.lyrics_usages, key=lambda item: item.lyrics_version_id):
            version = await uow.lyrics_versions.get_published(usage.lyrics_version_id, for_update=True)
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
        music: RecordingUnitOfWork,
        people: PeopleCatalogUnitOfWork,
        recording: Recording,
    ) -> bool:
        primary_credits = sorted(
            (credit for credit in recording.credits if credit.billing_role is BillingRole.PRIMARY),
            key=lambda credit: (credit.target_kind.value, credit.target_id),
        )
        for credit in primary_credits:
            match credit.target_kind:
                case RecordingCreditTargetKind.PERSON:
                    if await people.persons.get_published(credit.target_id, for_update=True) is not None:
                        return True
                case RecordingCreditTargetKind.GROUP:
                    if await music.groups.get_published(credit.target_id, for_update=True) is not None:
                        return True
        return False
