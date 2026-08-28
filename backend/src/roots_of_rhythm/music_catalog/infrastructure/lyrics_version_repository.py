from typing import TYPE_CHECKING

from sqlalchemy import case, select

from roots_of_rhythm.infrastructure.database import apply_write_lock
from roots_of_rhythm.music_catalog.domain import EditorialStatus, LyricsUsageKind, LyricsVersion
from roots_of_rhythm.music_catalog.infrastructure.mapping import (
    lyrics_version_from_record,
    record_from_lyrics_version,
    update_lyrics_version_record,
)
from roots_of_rhythm.music_catalog.infrastructure.models import LyricsVersionRecord

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyLyricsVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, version: LyricsVersion) -> None:
        self._session.add(record_from_lyrics_version(version))

    async def get(self, version_id: UUID, *, for_update: bool = False) -> LyricsVersion | None:
        return await self._get(version_id, for_update=for_update)

    async def get_published(self, version_id: UUID, *, for_update: bool = False) -> LyricsVersion | None:
        return await self._get(version_id, status=EditorialStatus.PUBLISHED, for_update=for_update)

    async def get_published_by_ids(self, version_ids: Collection[UUID]) -> dict[UUID, LyricsVersion]:
        ids = set(version_ids)
        if not ids:
            return {}
        statement = select(LyricsVersionRecord).where(
            LyricsVersionRecord.id.in_(ids),
            LyricsVersionRecord.editorial_status == EditorialStatus.PUBLISHED.value,
            LyricsVersionRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        return {record.id: lyrics_version_from_record(record) for record in result.scalars()}

    async def list_published_for_work(self, work_id: UUID) -> list[LyricsVersion]:
        usage_order = case(
            (LyricsVersionRecord.usage_kind == LyricsUsageKind.PERFORMABLE.value, 0),
            else_=1,
        )
        statement = (
            select(LyricsVersionRecord)
            .where(
                LyricsVersionRecord.work_id == work_id,
                LyricsVersionRecord.editorial_status == EditorialStatus.PUBLISHED.value,
                LyricsVersionRecord.deleted.is_(False),
            )
            .order_by(usage_order, LyricsVersionRecord.language_tag, LyricsVersionRecord.label, LyricsVersionRecord.id)
        )
        result = await self._session.execute(statement)
        return [lyrics_version_from_record(record) for record in result.scalars()]

    async def save(self, version: LyricsVersion) -> None:
        record = await self._get_record(version.id, for_update=True)
        if record is None:
            raise LookupError(str(version.id))
        update_lyrics_version_record(record, version)

    async def mark_deleted(self, version_id: UUID) -> None:
        record = await self._get_record(version_id, for_update=True)
        if record is None:
            raise LookupError(str(version_id))
        record.deleted = True

    async def _get(
        self,
        version_id: UUID,
        status: EditorialStatus | None = None,
        *,
        for_update: bool = False,
    ) -> LyricsVersion | None:
        record = await self._get_record(version_id, status=status, for_update=for_update)
        return None if record is None else lyrics_version_from_record(record)

    async def _get_record(
        self,
        version_id: UUID,
        *,
        status: EditorialStatus | None = None,
        for_update: bool = False,
    ) -> LyricsVersionRecord | None:
        statement = select(LyricsVersionRecord).where(
            LyricsVersionRecord.id == version_id,
            LyricsVersionRecord.deleted.is_(False),
        )
        if status is not None:
            statement = statement.where(LyricsVersionRecord.editorial_status == status.value)
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
