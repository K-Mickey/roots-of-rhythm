from typing import TYPE_CHECKING

from sqlalchemy import select

from roots_of_rhythm.infrastructure.database import apply_write_lock
from roots_of_rhythm.music_catalog.domain import EditorialStatus, GroupMembership
from roots_of_rhythm.music_catalog.infrastructure.mapping import (
    group_membership_from_record,
    record_from_group_membership,
    update_group_membership_record,
)
from roots_of_rhythm.music_catalog.infrastructure.models import GroupMembershipRecord

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyGroupMembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, membership: GroupMembership) -> None:
        self._session.add(record_from_group_membership(membership))

    async def get(self, membership_id: UUID, *, for_update: bool = False) -> GroupMembership | None:
        return await self._get(membership_id, for_update=for_update)

    async def get_published(self, membership_id: UUID, *, for_update: bool = False) -> GroupMembership | None:
        return await self._get(membership_id, status=EditorialStatus.PUBLISHED, for_update=for_update)

    async def list_published_by_group(self, group_id: UUID) -> list[GroupMembership]:
        statement = (
            select(GroupMembershipRecord)
            .where(
                GroupMembershipRecord.group_id == group_id,
                GroupMembershipRecord.editorial_status == EditorialStatus.PUBLISHED.value,
                GroupMembershipRecord.deleted.is_(False),
            )
            .order_by(GroupMembershipRecord.id)
        )
        result = await self._session.execute(statement)
        return [group_membership_from_record(record) for record in result.scalars()]

    async def save(self, membership: GroupMembership) -> None:
        record = await self._get_record(membership.id, for_update=True)
        if record is None:
            raise LookupError(str(membership.id))
        update_group_membership_record(record, membership)

    async def mark_deleted(self, membership_id: UUID) -> None:
        record = await self._get_record(membership_id, for_update=True)
        if record is None:
            raise LookupError(str(membership_id))
        record.deleted = True

    async def _get(
        self,
        membership_id: UUID,
        status: EditorialStatus | None = None,
        *,
        for_update: bool = False,
    ) -> GroupMembership | None:
        record = await self._get_record(membership_id, status=status, for_update=for_update)
        return None if record is None else group_membership_from_record(record)

    async def _get_record(
        self,
        membership_id: UUID,
        *,
        status: EditorialStatus | None = None,
        for_update: bool = False,
    ) -> GroupMembershipRecord | None:
        statement = select(GroupMembershipRecord).where(
            GroupMembershipRecord.id == membership_id,
            GroupMembershipRecord.deleted.is_(False),
        )
        if status is not None:
            statement = statement.where(GroupMembershipRecord.editorial_status == status.value)
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
