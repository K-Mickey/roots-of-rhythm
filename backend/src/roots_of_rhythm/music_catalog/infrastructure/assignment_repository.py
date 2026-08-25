from typing import TYPE_CHECKING

from sqlalchemy import select

from roots_of_rhythm.infrastructure.database import apply_write_lock
from roots_of_rhythm.music_catalog.domain import ClassificationAssignment, ClassificationTargetKind, EditorialStatus
from roots_of_rhythm.music_catalog.infrastructure.mapping import (
    assignment_from_record,
    record_from_assignment,
    update_assignment_record,
)
from roots_of_rhythm.music_catalog.infrastructure.models import ClassificationAssignmentRecord

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyClassificationAssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, assignment: ClassificationAssignment) -> None:
        self._session.add(record_from_assignment(assignment))

    async def get(self, assignment_id: UUID, *, for_update: bool = False) -> ClassificationAssignment | None:
        statement = select(ClassificationAssignmentRecord).where(
            ClassificationAssignmentRecord.id == assignment_id,
            ClassificationAssignmentRecord.deleted.is_(False),
        )
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        return None if record is None else assignment_from_record(record)

    async def list_published_for_person(self, person_id: UUID) -> list[ClassificationAssignment]:
        statement = select(ClassificationAssignmentRecord).where(
            ClassificationAssignmentRecord.target_kind == ClassificationTargetKind.PERSON.value,
            ClassificationAssignmentRecord.target_id == person_id,
            ClassificationAssignmentRecord.editorial_status == EditorialStatus.PUBLISHED.value,
            ClassificationAssignmentRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        return [assignment_from_record(record) for record in result.scalars()]

    async def list_published_for_group(self, group_id: UUID) -> list[ClassificationAssignment]:
        statement = select(ClassificationAssignmentRecord).where(
            ClassificationAssignmentRecord.target_kind == ClassificationTargetKind.GROUP.value,
            ClassificationAssignmentRecord.target_id == group_id,
            ClassificationAssignmentRecord.editorial_status == EditorialStatus.PUBLISHED.value,
            ClassificationAssignmentRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        return [assignment_from_record(record) for record in result.scalars()]

    async def save(self, assignment: ClassificationAssignment) -> None:
        statement = select(ClassificationAssignmentRecord).where(
            ClassificationAssignmentRecord.id == assignment.id,
            ClassificationAssignmentRecord.deleted.is_(False),
        )
        statement = apply_write_lock(statement, for_update=True)
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        if record is None:
            raise LookupError(str(assignment.id))
        update_assignment_record(record, assignment)
