from typing import TYPE_CHECKING

from sqlalchemy import or_, select

from roots_of_rhythm.infrastructure.database import apply_write_lock
from roots_of_rhythm.music_catalog.domain import EditorialStatus, WorkRelation
from roots_of_rhythm.music_catalog.infrastructure.mapping import (
    record_from_work_relation,
    update_work_relation_record,
    work_relation_from_record,
)
from roots_of_rhythm.music_catalog.infrastructure.models import WorkRelationRecord

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyWorkRelationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, relation: WorkRelation) -> None:
        self._session.add(record_from_work_relation(relation))

    async def get(self, relation_id: UUID, *, for_update: bool = False) -> WorkRelation | None:
        return await self._get(relation_id, for_update=for_update)

    async def get_published(self, relation_id: UUID, *, for_update: bool = False) -> WorkRelation | None:
        return await self._get(relation_id, status=EditorialStatus.PUBLISHED, for_update=for_update)

    async def list_published_for_work(self, work_id: UUID) -> list[WorkRelation]:
        statement = (
            select(WorkRelationRecord)
            .where(
                or_(
                    WorkRelationRecord.source_work_id == work_id,
                    WorkRelationRecord.target_work_id == work_id,
                ),
                WorkRelationRecord.editorial_status == EditorialStatus.PUBLISHED.value,
                WorkRelationRecord.deleted.is_(False),
            )
            .order_by(WorkRelationRecord.relation_type, WorkRelationRecord.id)
        )
        result = await self._session.execute(statement)
        return [work_relation_from_record(record) for record in result.scalars()]

    async def save(self, relation: WorkRelation) -> None:
        record = await self._get_record(relation.id, for_update=True)
        if record is None:
            raise LookupError(str(relation.id))
        update_work_relation_record(record, relation)

    async def mark_deleted(self, relation_id: UUID) -> None:
        record = await self._get_record(relation_id, for_update=True)
        if record is None:
            raise LookupError(str(relation_id))
        record.deleted = True

    async def _get(
        self,
        relation_id: UUID,
        status: EditorialStatus | None = None,
        *,
        for_update: bool = False,
    ) -> WorkRelation | None:
        record = await self._get_record(relation_id, status=status, for_update=for_update)
        return None if record is None else work_relation_from_record(record)

    async def _get_record(
        self,
        relation_id: UUID,
        *,
        status: EditorialStatus | None = None,
        for_update: bool = False,
    ) -> WorkRelationRecord | None:
        statement = select(WorkRelationRecord).where(
            WorkRelationRecord.id == relation_id,
            WorkRelationRecord.deleted.is_(False),
        )
        if status is not None:
            statement = statement.where(WorkRelationRecord.editorial_status == status.value)
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
