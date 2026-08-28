from typing import TYPE_CHECKING

from sqlalchemy import select

from roots_of_rhythm.historical_knowledge.domain import EditorialStatus, ListeningGuide, ListeningObservation
from roots_of_rhythm.historical_knowledge.infrastructure.models import ListeningGuideRecord, ListeningObservationRecord
from roots_of_rhythm.infrastructure.database import apply_write_lock

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyListeningGuideRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, guide: ListeningGuide) -> None:
        self._session.add(
            ListeningGuideRecord(
                id=guide.id, recording_id=guide.recording_id, editorial_status=guide.editorial_status.value
            )
        )
        await self._session.flush()
        self._session.add_all([_observation_record(guide.id, item) for item in guide.observations])

    async def get(self, guide_id: UUID, *, for_update: bool = False) -> ListeningGuide | None:
        return await self._get(guide_id=guide_id, for_update=for_update)

    async def get_published_for_recording(self, recording_id: UUID) -> ListeningGuide | None:
        return await self._get(recording_id=recording_id, published=True)

    async def save(self, guide: ListeningGuide) -> None:
        statement = apply_write_lock(
            select(ListeningGuideRecord).where(
                ListeningGuideRecord.id == guide.id, ListeningGuideRecord.deleted.is_(False)
            ),
            for_update=True,
        )
        record = (await self._session.execute(statement)).scalar_one_or_none()
        if record is None:
            raise LookupError(str(guide.id))
        record.editorial_status = guide.editorial_status.value
        stored = {
            row.id: row
            for row in await self._session.scalars(
                select(ListeningObservationRecord).where(ListeningObservationRecord.guide_id == guide.id)
            )
        }
        active_ids = {item.id for item in guide.observations}
        for row in stored.values():
            row.deleted = row.id not in active_ids
        for observation in guide.observations:
            stored_row = stored.get(observation.id)
            if stored_row is not None:
                _update_observation(stored_row, observation)
                stored_row.deleted = False
            else:
                self._session.add(_observation_record(guide.id, observation))

    async def mark_deleted(self, guide_id: UUID) -> None:
        guide = await self._guide_record(guide_id, for_update=True)
        if guide is None:
            raise LookupError(str(guide_id))
        guide.deleted = True

    async def _get(
        self,
        *,
        guide_id: UUID | None = None,
        recording_id: UUID | None = None,
        published: bool = False,
        for_update: bool = False,
    ) -> ListeningGuide | None:
        statement = select(ListeningGuideRecord).where(ListeningGuideRecord.deleted.is_(False))
        if guide_id is not None:
            statement = statement.where(ListeningGuideRecord.id == guide_id)
        if recording_id is not None:
            statement = statement.where(ListeningGuideRecord.recording_id == recording_id)
        if published:
            statement = statement.where(ListeningGuideRecord.editorial_status == EditorialStatus.PUBLISHED.value)
        record = (await self._session.execute(apply_write_lock(statement, for_update=for_update))).scalar_one_or_none()
        if record is None:
            return None
        observations = list(
            await self._session.scalars(
                select(ListeningObservationRecord)
                .where(ListeningObservationRecord.guide_id == record.id, ListeningObservationRecord.deleted.is_(False))
                .order_by(ListeningObservationRecord.position)
            )
        )
        return ListeningGuide(
            record.id,
            record.recording_id,
            tuple(_observation(item) for item in observations),
            EditorialStatus(record.editorial_status),
        )

    async def _guide_record(self, guide_id: UUID, *, for_update: bool) -> ListeningGuideRecord | None:
        statement = select(ListeningGuideRecord).where(
            ListeningGuideRecord.id == guide_id, ListeningGuideRecord.deleted.is_(False)
        )
        return (await self._session.execute(apply_write_lock(statement, for_update=for_update))).scalar_one_or_none()


def _observation_record(guide_id: UUID, item: ListeningObservation) -> ListeningObservationRecord:
    return ListeningObservationRecord(
        guide_id=guide_id,
        **{
            name: getattr(item, name)
            for name in (
                "id",
                "feature",
                "explanation",
                "context",
                "author_id",
                "authored_at",
                "start_seconds",
                "end_seconds",
                "position",
            )
        },
    )


def _update_observation(row: ListeningObservationRecord, item: ListeningObservation) -> None:
    for name in (
        "feature",
        "explanation",
        "context",
        "author_id",
        "authored_at",
        "start_seconds",
        "end_seconds",
        "position",
    ):
        setattr(row, name, getattr(item, name))


def _observation(row: ListeningObservationRecord) -> ListeningObservation:
    return ListeningObservation(
        **{
            name: getattr(row, name)
            for name in (
                "id",
                "feature",
                "explanation",
                "context",
                "author_id",
                "authored_at",
                "start_seconds",
                "end_seconds",
                "position",
            )
        }
    )
