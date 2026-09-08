from typing import TYPE_CHECKING

from sqlalchemy import select, update

from roots_of_rhythm.historical_knowledge.domain import FragmentReviewStatus
from roots_of_rhythm.historical_knowledge.infrastructure.mapping import (
    fragment_from_record,
    record_from_fragment,
    record_from_source,
    record_from_version,
    source_from_record,
    update_fragment_record,
    version_from_record,
)
from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    SourceFragmentRecord,
    SourceRecord,
    SourceVersionRecord,
)
from roots_of_rhythm.infrastructure.database import apply_write_lock

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from roots_of_rhythm.historical_knowledge.domain import (
        Source,
        SourceFragment,
        SourceVersion,
    )


class SqlAlchemySourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_source(self, source: Source) -> None:
        self._session.add(record_from_source(source))

    async def save_source(self, source: Source) -> None:
        statement = select(SourceRecord).where(
            SourceRecord.id == source.id,
            SourceRecord.deleted.is_(False),
        )
        statement = apply_write_lock(statement, for_update=True)
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        if record is None:
            raise LookupError(str(source.id))
        record.access_policy = source.access_policy.value

    async def add_version(self, version: SourceVersion) -> None:
        self._session.add(record_from_version(version))

    async def add_fragment(self, fragment: SourceFragment) -> None:
        self._session.add(record_from_fragment(fragment))

    async def get_source(self, source_id: UUID, *, for_update: bool = False) -> Source | None:
        statement = select(SourceRecord).where(
            SourceRecord.id == source_id,
            SourceRecord.deleted.is_(False),
        )
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        return None if record is None else source_from_record(record)

    async def get_sources_by_ids(self, source_ids: Collection[UUID]) -> dict[UUID, Source]:
        ids = set(source_ids)
        if not ids:
            return {}
        statement = select(SourceRecord).where(
            SourceRecord.id.in_(ids),
            SourceRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        return {record.id: source_from_record(record) for record in result.scalars()}

    async def get_version(self, version_id: UUID, *, for_update: bool = False) -> SourceVersion | None:
        statement = select(SourceVersionRecord).where(
            SourceVersionRecord.id == version_id,
            SourceVersionRecord.deleted.is_(False),
        )
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        return None if record is None else version_from_record(record)

    async def get_versions_by_ids(self, version_ids: Collection[UUID]) -> dict[UUID, SourceVersion]:
        ids = set(version_ids)
        if not ids:
            return {}
        statement = select(SourceVersionRecord).where(
            SourceVersionRecord.id.in_(ids),
            SourceVersionRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        return {record.id: version_from_record(record) for record in result.scalars()}

    async def get_fragment(self, fragment_id: UUID, *, for_update: bool = False) -> SourceFragment | None:
        statement = select(SourceFragmentRecord).where(
            SourceFragmentRecord.id == fragment_id,
            SourceFragmentRecord.deleted.is_(False),
        )
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        return None if record is None else fragment_from_record(record)

    async def get_fragments_by_ids(
        self,
        fragment_ids: Collection[UUID],
        *,
        for_update: bool = False,
    ) -> dict[UUID, SourceFragment]:
        ids = set(fragment_ids)
        if not ids:
            return {}
        statement = (
            select(SourceFragmentRecord)
            .where(
                SourceFragmentRecord.id.in_(ids),
                SourceFragmentRecord.deleted.is_(False),
            )
            .order_by(SourceFragmentRecord.id)
        )
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        return {record.id: fragment_from_record(record) for record in result.scalars()}

    async def save_fragment(self, fragment: SourceFragment) -> None:
        statement = select(SourceFragmentRecord).where(
            SourceFragmentRecord.id == fragment.id,
            SourceFragmentRecord.deleted.is_(False),
        )
        statement = apply_write_lock(statement, for_update=True)
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        if record is None:
            raise LookupError(str(fragment.id))
        update_fragment_record(record, fragment)

    async def reviewed_source_ids_for_fragments(self, fragment_ids: Collection[UUID]) -> dict[UUID, UUID]:
        ids = set(fragment_ids)
        if not ids:
            return {}
        statement = (
            select(SourceFragmentRecord.id, SourceVersionRecord.source_id)
            .join(
                SourceVersionRecord,
                SourceVersionRecord.id == SourceFragmentRecord.source_version_id,
            )
            .where(
                SourceFragmentRecord.id.in_(ids),
                SourceFragmentRecord.deleted.is_(False),
                SourceFragmentRecord.review_status == FragmentReviewStatus.REVIEWED.value,
                SourceVersionRecord.deleted.is_(False),
            )
        )
        result = await self._session.execute(statement)
        return dict(result.tuples().all())

    async def mark_source_deleted(self, source_id: UUID) -> None:
        statement = select(SourceRecord).where(
            SourceRecord.id == source_id,
            SourceRecord.deleted.is_(False),
        )
        statement = apply_write_lock(statement, for_update=True)
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        if record is None:
            raise LookupError(str(source_id))
        record.deleted = True
        version_ids = list(
            (
                await self._session.execute(
                    select(SourceVersionRecord.id).where(
                        SourceVersionRecord.source_id == source_id,
                        SourceVersionRecord.deleted.is_(False),
                    )
                )
            ).scalars()
        )
        if version_ids:
            await self._session.execute(
                update(SourceVersionRecord).where(SourceVersionRecord.id.in_(version_ids)).values(deleted=True)
            )
            await self._session.execute(
                update(SourceFragmentRecord)
                .where(
                    SourceFragmentRecord.source_version_id.in_(version_ids),
                    SourceFragmentRecord.deleted.is_(False),
                )
                .values(deleted=True)
            )

    async def mark_version_deleted(self, version_id: UUID) -> None:
        statement = select(SourceVersionRecord).where(
            SourceVersionRecord.id == version_id,
            SourceVersionRecord.deleted.is_(False),
        )
        statement = apply_write_lock(statement, for_update=True)
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        if record is None:
            raise LookupError(str(version_id))
        record.deleted = True
        await self._session.execute(
            update(SourceFragmentRecord)
            .where(
                SourceFragmentRecord.source_version_id == version_id,
                SourceFragmentRecord.deleted.is_(False),
            )
            .values(deleted=True)
        )

    async def mark_fragment_deleted(self, fragment_id: UUID) -> None:
        statement = select(SourceFragmentRecord).where(
            SourceFragmentRecord.id == fragment_id,
            SourceFragmentRecord.deleted.is_(False),
        )
        statement = apply_write_lock(statement, for_update=True)
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        if record is None:
            raise LookupError(str(fragment_id))
        record.deleted = True
