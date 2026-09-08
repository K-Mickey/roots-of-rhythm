from collections.abc import Callable
from uuid import UUID, uuid7

from roots_of_rhythm.music_catalog.application.errors import (
    UniqueConstraintViolation,
    WorkCreditConflict,
    WorkCreditNotFound,
)
from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
from roots_of_rhythm.music_catalog.domain import WorkCredit, WorkCreditContent, WorkCreditRole

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


class WorkCreditService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self,
        work_id: UUID,
        person_id: UUID,
        role: WorkCreditRole,
        content: WorkCreditContent | None = None,
        *,
        credit_id: UUID | None = None,
    ) -> WorkCredit:
        async with self._uow_factory() as uow:
            credit = WorkCredit.create(
                credit_id or uuid7(),
                work_id,
                person_id,
                role,
                content,
            )
            await uow.work_credits.add(credit)
            await self._commit(uow)
            return credit

    async def replace_content(self, credit_id: UUID, content: WorkCreditContent) -> WorkCredit:
        async with self._uow_factory() as uow:
            credit = await self._get(uow, credit_id, for_update=True)
            updated = credit.replace_content(content)
            try:
                await uow.work_credits.save(updated)
            except LookupError as error:
                raise WorkCreditNotFound(str(credit_id)) from error
            await self._commit(uow)
            return updated

    async def publish(self, credit_id: UUID) -> WorkCredit:
        return await self._change_status(credit_id, WorkCredit.publish)

    async def archive(self, credit_id: UUID) -> WorkCredit:
        return await self._change_status(credit_id, WorkCredit.archive)

    async def _change_status(
        self,
        credit_id: UUID,
        transition: Callable[[WorkCredit], WorkCredit],
    ) -> WorkCredit:
        async with self._uow_factory() as uow:
            credit = await self._get(uow, credit_id, for_update=True)
            updated = transition(credit)
            try:
                await uow.work_credits.save(updated)
            except LookupError as error:
                raise WorkCreditNotFound(str(credit_id)) from error
            await self._commit(uow)
            return updated

    @staticmethod
    async def _get(
        uow: MusicCatalogUnitOfWork,
        credit_id: UUID,
        *,
        for_update: bool = False,
    ) -> WorkCredit:
        credit = await uow.work_credits.get(credit_id, for_update=for_update)
        if credit is None:
            raise WorkCreditNotFound(str(credit_id))
        return credit

    @staticmethod
    async def _commit(uow: MusicCatalogUnitOfWork) -> None:
        try:
            await uow.commit()
        except UniqueConstraintViolation as error:
            raise WorkCreditConflict from error
