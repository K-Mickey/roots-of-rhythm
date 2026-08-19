from typing import TYPE_CHECKING

from sqlalchemy import select

from roots_of_rhythm.infrastructure.database import apply_write_lock
from roots_of_rhythm.people_catalog.domain import EditorialStatus, Person
from roots_of_rhythm.people_catalog.infrastructure.mapping import person_from_record, record_from_person, update_record
from roots_of_rhythm.people_catalog.infrastructure.models import PersonRecord

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyPersonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, person: Person) -> None:
        self._session.add(record_from_person(person))

    async def get(self, person_id: UUID, *, for_update: bool = False) -> Person | None:
        return await self._get(person_id, for_update=for_update)

    async def get_published(self, person_id: UUID, *, for_update: bool = False) -> Person | None:
        return await self._get(person_id, status=EditorialStatus.PUBLISHED, for_update=for_update)

    async def list_published(self) -> list[Person]:
        statement = (
            select(PersonRecord)
            .where(
                PersonRecord.editorial_status == EditorialStatus.PUBLISHED.value,
                PersonRecord.deleted.is_(False),
            )
            .order_by(PersonRecord.canonical_name)
        )
        result = await self._session.execute(statement)
        return [person_from_record(record) for record in result.scalars()]

    async def save(self, person: Person) -> None:
        record = await self._get_record(person.id, for_update=True)
        if record is None:
            raise LookupError(str(person.id))
        update_record(record, person)

    async def mark_deleted(self, person_id: UUID) -> None:
        record = await self._get_record(person_id, for_update=True)
        if record is None:
            raise LookupError(str(person_id))
        record.deleted = True

    async def _get(
        self,
        person_id: UUID,
        status: EditorialStatus | None = None,
        *,
        for_update: bool = False,
    ) -> Person | None:
        record = await self._get_record(person_id, status=status, for_update=for_update)
        return None if record is None else person_from_record(record)

    async def _get_record(
        self,
        person_id: UUID,
        *,
        status: EditorialStatus | None = None,
        for_update: bool = False,
    ) -> PersonRecord | None:
        statement = select(PersonRecord).where(PersonRecord.id == person_id, PersonRecord.deleted.is_(False))
        if status is not None:
            statement = statement.where(PersonRecord.editorial_status == status.value)
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
