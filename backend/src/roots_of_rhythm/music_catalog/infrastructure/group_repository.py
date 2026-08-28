from typing import TYPE_CHECKING

from sqlalchemy import select

if TYPE_CHECKING:
    from collections.abc import Collection

from roots_of_rhythm.infrastructure.database import apply_write_lock
from roots_of_rhythm.music_catalog.domain import EditorialStatus, Group
from roots_of_rhythm.music_catalog.infrastructure.mapping import (
    group_from_record,
    record_from_group,
    update_group_record,
)
from roots_of_rhythm.music_catalog.infrastructure.models import GroupRecord

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyGroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, group: Group) -> None:
        self._session.add(record_from_group(group))

    async def get(self, group_id: UUID, *, for_update: bool = False) -> Group | None:
        return await self._get(group_id, for_update=for_update)

    async def get_published(self, group_id: UUID, *, for_update: bool = False) -> Group | None:
        return await self._get(group_id, status=EditorialStatus.PUBLISHED, for_update=for_update)

    async def get_published_by_ids(self, group_ids: Collection[UUID]) -> dict[UUID, Group]:
        ids = set(group_ids)
        if not ids:
            return {}
        statement = select(GroupRecord).where(
            GroupRecord.id.in_(ids),
            GroupRecord.editorial_status == EditorialStatus.PUBLISHED.value,
            GroupRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        return {record.id: group_from_record(record) for record in result.scalars()}

    async def list_published(self) -> list[Group]:
        statement = (
            select(GroupRecord)
            .where(
                GroupRecord.editorial_status == EditorialStatus.PUBLISHED.value,
                GroupRecord.deleted.is_(False),
            )
            .order_by(GroupRecord.canonical_name)
        )
        result = await self._session.execute(statement)
        return [group_from_record(record) for record in result.scalars()]

    async def save(self, group: Group) -> None:
        record = await self._get_record(group.id, for_update=True)
        if record is None:
            raise LookupError(str(group.id))
        update_group_record(record, group)

    async def mark_deleted(self, group_id: UUID) -> None:
        record = await self._get_record(group_id, for_update=True)
        if record is None:
            raise LookupError(str(group_id))
        record.deleted = True

    async def _get(
        self,
        group_id: UUID,
        status: EditorialStatus | None = None,
        *,
        for_update: bool = False,
    ) -> Group | None:
        record = await self._get_record(group_id, status=status, for_update=for_update)
        return None if record is None else group_from_record(record)

    async def _get_record(
        self,
        group_id: UUID,
        *,
        status: EditorialStatus | None = None,
        for_update: bool = False,
    ) -> GroupRecord | None:
        statement = select(GroupRecord).where(GroupRecord.id == group_id, GroupRecord.deleted.is_(False))
        if status is not None:
            statement = statement.where(GroupRecord.editorial_status == status.value)
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
