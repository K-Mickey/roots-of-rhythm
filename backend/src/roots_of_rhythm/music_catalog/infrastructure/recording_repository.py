from collections import defaultdict
from typing import TYPE_CHECKING

from sqlalchemy import select

from roots_of_rhythm.infrastructure.database import apply_write_lock
from roots_of_rhythm.music_catalog.domain import EditorialStatus, Recording
from roots_of_rhythm.music_catalog.infrastructure.mapping import (
    record_from_recording,
    recording_from_records,
    records_from_recording_children,
    update_recording_record,
)
from roots_of_rhythm.music_catalog.infrastructure.models import (
    RecordingCreditRecord,
    RecordingLyricsUsageRecord,
    RecordingRecord,
    RecordingWorkUsageRecord,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyRecordingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, recording: Recording) -> None:
        credit_records, usages, lyrics_usages = records_from_recording_children(recording)
        self._session.add(record_from_recording(recording))
        await self._session.flush()
        self._session.add_all([*credit_records, *usages, *lyrics_usages])

    async def get(self, recording_id: UUID, *, for_update: bool = False) -> Recording | None:
        return await self._get(recording_id, for_update=for_update)

    async def get_published(self, recording_id: UUID, *, for_update: bool = False) -> Recording | None:
        return await self._get(recording_id, status=EditorialStatus.PUBLISHED, for_update=for_update)

    async def list_published(self) -> list[Recording]:
        records = list(
            await self._session.scalars(
                select(RecordingRecord)
                .where(
                    RecordingRecord.editorial_status == EditorialStatus.PUBLISHED.value,
                    RecordingRecord.deleted.is_(False),
                )
                .order_by(RecordingRecord.title, RecordingRecord.id)
            )
        )
        if not records:
            return []
        ids = [record.id for record in records]
        credits = await self._active_children(RecordingCreditRecord, ids)
        work_usages = await self._active_children(RecordingWorkUsageRecord, ids)
        lyrics_usages = await self._active_children(RecordingLyricsUsageRecord, ids)
        return [
            recording_from_records(
                record,
                credits[record.id],
                sorted(work_usages[record.id], key=lambda item: (item.position is None, item.position, item.id)),
                sorted(lyrics_usages[record.id], key=lambda item: (item.position, item.id)),
            )
            for record in records
        ]

    async def save(self, recording: Recording) -> None:
        record = await self._get_record(recording.id, for_update=True)
        if record is None:
            raise LookupError(str(recording.id))
        update_recording_record(record, recording)
        await self._replace_children(recording)

    async def save_status(self, recording: Recording) -> None:
        record = await self._get_record(recording.id, for_update=True)
        if record is None:
            raise LookupError(str(recording.id))
        record.editorial_status = recording.editorial_status.value

    async def mark_deleted(self, recording_id: UUID) -> None:
        record = await self._get_record(recording_id, for_update=True)
        if record is None:
            raise LookupError(str(recording_id))
        record.deleted = True

    async def _get(
        self,
        recording_id: UUID,
        status: EditorialStatus | None = None,
        *,
        for_update: bool = False,
    ) -> Recording | None:
        record = await self._get_record(recording_id, status=status, for_update=for_update)
        if record is None:
            return None
        credit_records = await self._session.scalars(
            select(RecordingCreditRecord)
            .where(
                RecordingCreditRecord.recording_id == recording_id,
                RecordingCreditRecord.deleted.is_(False),
            )
            .order_by(RecordingCreditRecord.id)
        )
        usages = await self._session.scalars(
            select(RecordingWorkUsageRecord)
            .where(
                RecordingWorkUsageRecord.recording_id == recording_id,
                RecordingWorkUsageRecord.deleted.is_(False),
            )
            .order_by(RecordingWorkUsageRecord.position.nulls_last(), RecordingWorkUsageRecord.id)
        )
        lyrics_usages = await self._session.scalars(
            select(RecordingLyricsUsageRecord)
            .where(
                RecordingLyricsUsageRecord.recording_id == recording_id,
                RecordingLyricsUsageRecord.deleted.is_(False),
            )
            .order_by(RecordingLyricsUsageRecord.position, RecordingLyricsUsageRecord.id)
        )
        return recording_from_records(record, list(credit_records), list(usages), list(lyrics_usages))

    async def _get_record(
        self,
        recording_id: UUID,
        *,
        status: EditorialStatus | None = None,
        for_update: bool = False,
    ) -> RecordingRecord | None:
        statement = select(RecordingRecord).where(
            RecordingRecord.id == recording_id,
            RecordingRecord.deleted.is_(False),
        )
        if status is not None:
            statement = statement.where(RecordingRecord.editorial_status == status.value)
        result = await self._session.execute(apply_write_lock(statement, for_update=for_update))
        return result.scalar_one_or_none()

    async def _active_children(self, model: type, recording_ids: list[UUID]) -> defaultdict[UUID, list]:
        grouped: defaultdict[UUID, list] = defaultdict(list)
        rows = await self._session.scalars(
            select(model).where(model.recording_id.in_(recording_ids), model.deleted.is_(False))
        )
        for row in rows:
            grouped[row.recording_id].append(row)
        return grouped

    async def _replace_children(self, recording: Recording) -> None:
        stored_credits = list(
            await self._session.scalars(
                select(RecordingCreditRecord).where(RecordingCreditRecord.recording_id == recording.id)
            )
        )
        stored_usages = list(
            await self._session.scalars(
                select(RecordingWorkUsageRecord).where(RecordingWorkUsageRecord.recording_id == recording.id)
            )
        )
        stored_lyrics_usages = list(
            await self._session.scalars(
                select(RecordingLyricsUsageRecord).where(RecordingLyricsUsageRecord.recording_id == recording.id)
            )
        )
        credit_records, usages, lyrics_usages = records_from_recording_children(recording)
        credit_by_id = {record.id: record for record in stored_credits}
        usage_by_id = {record.id: record for record in stored_usages}
        lyrics_usage_by_id = {record.id: record for record in stored_lyrics_usages}
        for stored_credit_record in stored_credits:
            stored_credit_record.deleted = True
        for stored_usage_record in stored_usages:
            stored_usage_record.deleted = True
        for stored_lyrics_usage in stored_lyrics_usages:
            stored_lyrics_usage.deleted = True
        await self._session.flush()

        for incoming_credit in credit_records:
            if (stored_credit := credit_by_id.get(incoming_credit.id)) is None:
                self._session.add(incoming_credit)
                continue
            stored_credit.target_kind = incoming_credit.target_kind
            stored_credit.target_id = incoming_credit.target_id
            stored_credit.billing_role = incoming_credit.billing_role
            stored_credit.contribution_kind = incoming_credit.contribution_kind
            stored_credit.instrument = incoming_credit.instrument
            stored_credit.credited_as = incoming_credit.credited_as
            stored_credit.deleted = False

        for incoming_usage in usages:
            if (stored_usage := usage_by_id.get(incoming_usage.id)) is None:
                self._session.add(incoming_usage)
                continue
            stored_usage.work_id = incoming_usage.work_id
            stored_usage.usage_kind = incoming_usage.usage_kind
            stored_usage.position = incoming_usage.position
            stored_usage.deleted = False

        for incoming_lyrics_usage in lyrics_usages:
            if (found_lyrics_usage := lyrics_usage_by_id.get(incoming_lyrics_usage.id)) is None:
                self._session.add(incoming_lyrics_usage)
                continue
            found_lyrics_usage.lyrics_version_id = incoming_lyrics_usage.lyrics_version_id
            found_lyrics_usage.position = incoming_lyrics_usage.position
            found_lyrics_usage.deleted = False
