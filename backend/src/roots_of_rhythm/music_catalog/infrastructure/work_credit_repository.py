from typing import TYPE_CHECKING

from sqlalchemy import select

from roots_of_rhythm.infrastructure.database import apply_write_lock
from roots_of_rhythm.music_catalog.domain import EditorialStatus, WorkCredit
from roots_of_rhythm.music_catalog.infrastructure.mapping import (
    record_from_work_credit,
    update_work_credit_record,
    work_credit_from_record,
)
from roots_of_rhythm.music_catalog.infrastructure.models import WorkCreditRecord

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyWorkCreditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, credit: WorkCredit) -> None:
        self._session.add(record_from_work_credit(credit))

    async def get(self, credit_id: UUID, *, for_update: bool = False) -> WorkCredit | None:
        return await self._get(credit_id, for_update=for_update)

    async def get_published(self, credit_id: UUID, *, for_update: bool = False) -> WorkCredit | None:
        return await self._get(credit_id, status=EditorialStatus.PUBLISHED, for_update=for_update)

    async def list_published_for_work(self, work_id: UUID) -> list[WorkCredit]:
        statement = (
            select(WorkCreditRecord)
            .where(
                WorkCreditRecord.work_id == work_id,
                WorkCreditRecord.editorial_status == EditorialStatus.PUBLISHED.value,
                WorkCreditRecord.deleted.is_(False),
            )
            .order_by(WorkCreditRecord.role, WorkCreditRecord.id)
        )
        result = await self._session.execute(statement)
        return [work_credit_from_record(record) for record in result.scalars()]

    async def save(self, credit: WorkCredit) -> None:
        record = await self._get_record(credit.id, for_update=True)
        if record is None:
            raise LookupError(str(credit.id))
        update_work_credit_record(record, credit)

    async def mark_deleted(self, credit_id: UUID) -> None:
        record = await self._get_record(credit_id, for_update=True)
        if record is None:
            raise LookupError(str(credit_id))
        record.deleted = True

    async def _get(
        self,
        credit_id: UUID,
        status: EditorialStatus | None = None,
        *,
        for_update: bool = False,
    ) -> WorkCredit | None:
        record = await self._get_record(credit_id, status=status, for_update=for_update)
        return None if record is None else work_credit_from_record(record)

    async def _get_record(
        self,
        credit_id: UUID,
        *,
        status: EditorialStatus | None = None,
        for_update: bool = False,
    ) -> WorkCreditRecord | None:
        statement = select(WorkCreditRecord).where(
            WorkCreditRecord.id == credit_id,
            WorkCreditRecord.deleted.is_(False),
        )
        if status is not None:
            statement = statement.where(WorkCreditRecord.editorial_status == status.value)
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
