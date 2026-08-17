from typing import TYPE_CHECKING

from sqlalchemy import func, select

from roots_of_rhythm.music_catalog.domain import ClassificationKind, EditorialStatus, Genre
from roots_of_rhythm.music_catalog.infrastructure.mapping import genre_from_record, record_from_genre, update_record
from roots_of_rhythm.music_catalog.infrastructure.models import ClassificationConceptRecord

if TYPE_CHECKING:
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

    async def save(self, genre: Genre) -> None:
        record = await self._get_record(genre.id)
        if record is None:
            raise LookupError(str(genre.id))
        update_record(record, genre)

    async def canonical_name_exists(self, canonical_name: str, *, excluding: UUID | None = None) -> bool:
        statement = select(ClassificationConceptRecord.id).where(
            ClassificationConceptRecord.kind == ClassificationKind.GENRE.value,
            func.lower(ClassificationConceptRecord.canonical_name) == canonical_name.lower(),
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
        )
        if status is not None:
            statement = statement.where(ClassificationConceptRecord.editorial_status == status.value)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
