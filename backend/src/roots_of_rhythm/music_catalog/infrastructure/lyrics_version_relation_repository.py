from typing import TYPE_CHECKING

from sqlalchemy import or_, select

from roots_of_rhythm.infrastructure.database import apply_write_lock
from roots_of_rhythm.music_catalog.domain import EditorialStatus, LyricsVersionRelation
from roots_of_rhythm.music_catalog.infrastructure.mapping import (
    lyrics_version_relation_from_record,
    record_from_lyrics_version_relation,
    update_lyrics_version_relation_record,
)
from roots_of_rhythm.music_catalog.infrastructure.models import LyricsVersionRelationRecord

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyLyricsVersionRelationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, relation: LyricsVersionRelation) -> None:
        self._session.add(record_from_lyrics_version_relation(relation))

    async def get(self, relation_id: UUID, *, for_update: bool = False) -> LyricsVersionRelation | None:
        return await self._get(relation_id, for_update=for_update)

    async def get_published(self, relation_id: UUID, *, for_update: bool = False) -> LyricsVersionRelation | None:
        return await self._get(relation_id, status=EditorialStatus.PUBLISHED, for_update=for_update)

    async def list_published_for_version(self, lyrics_version_id: UUID) -> list[LyricsVersionRelation]:
        statement = (
            select(LyricsVersionRelationRecord)
            .where(
                or_(
                    LyricsVersionRelationRecord.source_lyrics_version_id == lyrics_version_id,
                    LyricsVersionRelationRecord.target_lyrics_version_id == lyrics_version_id,
                ),
                LyricsVersionRelationRecord.editorial_status == EditorialStatus.PUBLISHED.value,
                LyricsVersionRelationRecord.deleted.is_(False),
            )
            .order_by(LyricsVersionRelationRecord.relation_type, LyricsVersionRelationRecord.id)
        )
        result = await self._session.execute(statement)
        return [lyrics_version_relation_from_record(record) for record in result.scalars()]

    async def save(self, relation: LyricsVersionRelation) -> None:
        record = await self._get_record(relation.id, for_update=True)
        if record is None:
            raise LookupError(str(relation.id))
        update_lyrics_version_relation_record(record, relation)

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
    ) -> LyricsVersionRelation | None:
        record = await self._get_record(relation_id, status=status, for_update=for_update)
        return None if record is None else lyrics_version_relation_from_record(record)

    async def _get_record(
        self,
        relation_id: UUID,
        *,
        status: EditorialStatus | None = None,
        for_update: bool = False,
    ) -> LyricsVersionRelationRecord | None:
        statement = select(LyricsVersionRelationRecord).where(
            LyricsVersionRelationRecord.id == relation_id,
            LyricsVersionRelationRecord.deleted.is_(False),
        )
        if status is not None:
            statement = statement.where(LyricsVersionRelationRecord.editorial_status == status.value)
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
