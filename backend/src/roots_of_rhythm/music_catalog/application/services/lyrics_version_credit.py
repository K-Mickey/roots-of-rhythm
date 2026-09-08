from collections.abc import Callable
from uuid import UUID, uuid7

from roots_of_rhythm.music_catalog.application.errors import (
    LyricsVersionCreditConflict,
    LyricsVersionCreditNotFound,
    UniqueConstraintViolation,
)
from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
from roots_of_rhythm.music_catalog.domain import LyricsVersionCredit, LyricsVersionCreditContent, WorkCreditRole

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


class LyricsVersionCreditService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self,
        lyrics_version_id: UUID,
        person_id: UUID,
        role: WorkCreditRole,
        content: LyricsVersionCreditContent | None = None,
        *,
        credit_id: UUID | None = None,
    ) -> LyricsVersionCredit:
        async with self._uow_factory() as uow:
            credit = LyricsVersionCredit.create(
                credit_id or uuid7(),
                lyrics_version_id,
                person_id,
                role,
                content,
            )
            await uow.lyrics_version_credits.add(credit)
            await self._commit(uow)
            return credit

    async def replace_content(self, credit_id: UUID, content: LyricsVersionCreditContent) -> LyricsVersionCredit:
        async with self._uow_factory() as uow:
            credit = await self._get(uow, credit_id, for_update=True)
            updated = credit.replace_content(content)
            try:
                await uow.lyrics_version_credits.save(updated)
            except LookupError as error:
                raise LyricsVersionCreditNotFound(str(credit_id)) from error
            await self._commit(uow)
            return updated

    async def publish(self, credit_id: UUID) -> LyricsVersionCredit:
        return await self._change_status(credit_id, LyricsVersionCredit.publish)

    async def archive(self, credit_id: UUID) -> LyricsVersionCredit:
        return await self._change_status(credit_id, LyricsVersionCredit.archive)

    async def _change_status(
        self,
        credit_id: UUID,
        transition: Callable[[LyricsVersionCredit], LyricsVersionCredit],
    ) -> LyricsVersionCredit:
        async with self._uow_factory() as uow:
            credit = await self._get(uow, credit_id, for_update=True)
            updated = transition(credit)
            try:
                await uow.lyrics_version_credits.save(updated)
            except LookupError as error:
                raise LyricsVersionCreditNotFound(str(credit_id)) from error
            await self._commit(uow)
            return updated

    @staticmethod
    async def _get(
        uow: MusicCatalogUnitOfWork,
        credit_id: UUID,
        *,
        for_update: bool = False,
    ) -> LyricsVersionCredit:
        credit = await uow.lyrics_version_credits.get(credit_id, for_update=for_update)
        if credit is None:
            raise LyricsVersionCreditNotFound(str(credit_id))
        return credit

    @staticmethod
    async def _commit(uow: MusicCatalogUnitOfWork) -> None:
        try:
            await uow.commit()
        except UniqueConstraintViolation as error:
            raise LyricsVersionCreditConflict from error
