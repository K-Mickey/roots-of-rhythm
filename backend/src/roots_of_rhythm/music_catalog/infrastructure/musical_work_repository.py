from typing import TYPE_CHECKING

from sqlalchemy import select

from roots_of_rhythm.infrastructure.database import apply_write_lock
from roots_of_rhythm.music_catalog.domain import EditorialStatus, MusicalWork
from roots_of_rhythm.music_catalog.infrastructure.mapping import (
    musical_work_from_record,
    record_from_musical_work,
    update_musical_work_record,
)
from roots_of_rhythm.music_catalog.infrastructure.models import MusicalWorkRecord

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyMusicalWorkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, work: MusicalWork) -> None:
        self._session.add(record_from_musical_work(work))

    async def get(self, work_id: UUID, *, for_update: bool = False) -> MusicalWork | None:
        return await self._get(work_id, for_update=for_update)

    async def get_published(self, work_id: UUID, *, for_update: bool = False) -> MusicalWork | None:
        return await self._get(work_id, status=EditorialStatus.PUBLISHED, for_update=for_update)

    async def get_published_by_ids(self, work_ids: Collection[UUID]) -> dict[UUID, MusicalWork]:
        ids = set(work_ids)
        if not ids:
            return {}
        statement = select(MusicalWorkRecord).where(
            MusicalWorkRecord.id.in_(ids),
            MusicalWorkRecord.editorial_status == EditorialStatus.PUBLISHED.value,
            MusicalWorkRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        return {record.id: musical_work_from_record(record) for record in result.scalars()}

    async def list_published(self) -> list[MusicalWork]:
        statement = (
            select(MusicalWorkRecord)
            .where(
                MusicalWorkRecord.editorial_status == EditorialStatus.PUBLISHED.value,
                MusicalWorkRecord.deleted.is_(False),
            )
            .order_by(MusicalWorkRecord.canonical_title)
        )
        result = await self._session.execute(statement)
        return [musical_work_from_record(record) for record in result.scalars()]

    async def save(self, work: MusicalWork) -> None:
        record = await self._get_record(work.id, for_update=True)
        if record is None:
            raise LookupError(str(work.id))
        update_musical_work_record(record, work)

    async def mark_deleted(self, work_id: UUID) -> None:
        record = await self._get_record(work_id, for_update=True)
        if record is None:
            raise LookupError(str(work_id))
        record.deleted = True

    async def _get(
        self,
        work_id: UUID,
        status: EditorialStatus | None = None,
        *,
        for_update: bool = False,
    ) -> MusicalWork | None:
        record = await self._get_record(work_id, status=status, for_update=for_update)
        return None if record is None else musical_work_from_record(record)

    async def _get_record(
        self,
        work_id: UUID,
        *,
        status: EditorialStatus | None = None,
        for_update: bool = False,
    ) -> MusicalWorkRecord | None:
        statement = select(MusicalWorkRecord).where(
            MusicalWorkRecord.id == work_id,
            MusicalWorkRecord.deleted.is_(False),
        )
        if status is not None:
            statement = statement.where(MusicalWorkRecord.editorial_status == status.value)
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
