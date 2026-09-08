from collections.abc import Callable
from uuid import UUID, uuid7

from roots_of_rhythm.music_catalog.application.errors import (
    LyricsVersionConflict,
    LyricsVersionNotFound,
    UniqueConstraintViolation,
)
from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
from roots_of_rhythm.music_catalog.domain import LyricsVersion, LyricsVersionContent

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


class LyricsVersionService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self,
        work_id: UUID,
        source_version_id: UUID,
        content: LyricsVersionContent,
        *,
        version_id: UUID | None = None,
    ) -> LyricsVersion:
        async with self._uow_factory() as uow:
            version = LyricsVersion.create(
                version_id or uuid7(),
                work_id,
                source_version_id,
                content,
            )
            await uow.lyrics_versions.add(version)
            await self._commit(uow)
            return version

    async def replace_content(self, version_id: UUID, content: LyricsVersionContent) -> LyricsVersion:
        async with self._uow_factory() as uow:
            version = await self._get(uow, version_id, for_update=True)
            updated = version.replace_content(content)
            try:
                await uow.lyrics_versions.save(updated)
            except LookupError as error:
                raise LyricsVersionNotFound(str(version_id)) from error
            await self._commit(uow)
            return updated

    async def publish(self, version_id: UUID) -> LyricsVersion:
        return await self._change_status(version_id, LyricsVersion.publish)

    async def archive(self, version_id: UUID) -> LyricsVersion:
        return await self._change_status(version_id, LyricsVersion.archive)

    async def submit_for_review(self, version_id: UUID) -> LyricsVersion:
        return await self._change_status(version_id, LyricsVersion.submit_for_review)

    async def _change_status(
        self,
        version_id: UUID,
        transition: Callable[[LyricsVersion], LyricsVersion],
    ) -> LyricsVersion:
        async with self._uow_factory() as uow:
            version = await self._get(uow, version_id, for_update=True)
            updated = transition(version)
            try:
                await uow.lyrics_versions.save(updated)
            except LookupError as error:
                raise LyricsVersionNotFound(str(version_id)) from error
            await self._commit(uow)
            return updated

    @staticmethod
    async def _get(
        uow: MusicCatalogUnitOfWork,
        version_id: UUID,
        *,
        for_update: bool = False,
    ) -> LyricsVersion:
        version = await uow.lyrics_versions.get(version_id, for_update=for_update)
        if version is None:
            raise LyricsVersionNotFound(str(version_id))
        return version

    @staticmethod
    async def _commit(uow: MusicCatalogUnitOfWork) -> None:
        try:
            await uow.commit()
        except UniqueConstraintViolation as error:
            raise LyricsVersionConflict from error
