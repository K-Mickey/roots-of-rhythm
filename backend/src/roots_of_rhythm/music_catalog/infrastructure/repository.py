from typing import TYPE_CHECKING

from sqlalchemy import func, select

from roots_of_rhythm.music_catalog.domain import ClassificationKind, EditorialStatus, Genre
from roots_of_rhythm.music_catalog.infrastructure.mapping import genre_from_record, record_from_genre, update_record
from roots_of_rhythm.music_catalog.infrastructure.models import ClassificationConceptRecord

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyGenreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, genre: Genre) -> None:
        self._session.add(record_from_genre(genre))

    async def get(self, genre_id: UUID) -> Genre | None:
        return await self._get(genre_id)

    async def get_published(self, genre_id: UUID) -> Genre | None:
        return await self._get(genre_id, status=EditorialStatus.PUBLISHED)

    async def get_published_by_ids(self, genre_ids: Collection[UUID]) -> dict[UUID, Genre]:
        ids = set(genre_ids)
        if not ids:
            return {}
        statement = select(ClassificationConceptRecord).where(
            ClassificationConceptRecord.id.in_(ids),
            ClassificationConceptRecord.kind == ClassificationKind.GENRE.value,
            ClassificationConceptRecord.editorial_status == EditorialStatus.PUBLISHED.value,
            ClassificationConceptRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        return {record.id: genre_from_record(record) for record in result.scalars()}

    async def list_published(self) -> list[Genre]:
        statement = (
            select(ClassificationConceptRecord)
            .where(
                ClassificationConceptRecord.kind == ClassificationKind.GENRE.value,
                ClassificationConceptRecord.editorial_status == EditorialStatus.PUBLISHED.value,
                ClassificationConceptRecord.deleted.is_(False),
            )
            .order_by(ClassificationConceptRecord.canonical_name)
        )
        result = await self._session.execute(statement)
        return [genre_from_record(record) for record in result.scalars()]

    async def save(self, genre: Genre) -> None:
        record = await self._get_record(genre.id)
        if record is None:
            raise LookupError(str(genre.id))
        update_record(record, genre)

    async def mark_deleted(self, genre_id: UUID) -> None:
        record = await self._get_record(genre_id)
        if record is None:
            raise LookupError(str(genre_id))
        record.deleted = True

    async def published_among(self, genre_ids: Collection[UUID]) -> set[UUID]:
        ids = set(genre_ids)
        if not ids:
            return set()
        statement = select(ClassificationConceptRecord.id).where(
            ClassificationConceptRecord.id.in_(ids),
            ClassificationConceptRecord.kind == ClassificationKind.GENRE.value,
            ClassificationConceptRecord.editorial_status == EditorialStatus.PUBLISHED.value,
            ClassificationConceptRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        return set(result.scalars())

    async def canonical_name_exists(self, canonical_name: str, *, excluding: UUID | None = None) -> bool:
        statement = select(ClassificationConceptRecord.id).where(
            ClassificationConceptRecord.kind == ClassificationKind.GENRE.value,
            func.lower(ClassificationConceptRecord.canonical_name) == canonical_name.lower(),
            ClassificationConceptRecord.deleted.is_(False),
        )
        if excluding is not None:
            statement = statement.where(ClassificationConceptRecord.id != excluding)
        return await self._session.scalar(statement.limit(1)) is not None

    async def _get(self, genre_id: UUID, status: EditorialStatus | None = None) -> Genre | None:
        record = await self._get_record(genre_id, status=status)
        return None if record is None else genre_from_record(record)

    async def _get_record(
        self,
        genre_id: UUID,
        *,
        status: EditorialStatus | None = None,
    ) -> ClassificationConceptRecord | None:
        statement = select(ClassificationConceptRecord).where(
            ClassificationConceptRecord.id == genre_id,
            ClassificationConceptRecord.kind == ClassificationKind.GENRE.value,
            ClassificationConceptRecord.deleted.is_(False),
        )
        if status is not None:
            statement = statement.where(ClassificationConceptRecord.editorial_status == status.value)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
