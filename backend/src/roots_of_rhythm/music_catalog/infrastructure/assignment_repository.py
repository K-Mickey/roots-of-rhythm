from typing import TYPE_CHECKING

from psycopg import errors as psycopg_errors
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from roots_of_rhythm.infrastructure.database import apply_write_lock
from roots_of_rhythm.music_catalog.application.errors import UniqueConstraintViolation
from roots_of_rhythm.music_catalog.domain import ClassificationAssignment, ClassificationTargetKind, EditorialStatus
from roots_of_rhythm.music_catalog.infrastructure.mapping import (
    assignment_from_record,
    record_from_assignment,
    update_assignment_record,
)
from roots_of_rhythm.music_catalog.infrastructure.models import (
    CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT,
    ClassificationAssignmentRecord,
)

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyClassificationAssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, assignment: ClassificationAssignment) -> None:
        self._session.add(record_from_assignment(assignment))
        await self._flush_unique_constraint()

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

    async def list_published_for_work(self, work_id: UUID) -> list[ClassificationAssignment]:
        statement = select(ClassificationAssignmentRecord).where(
            ClassificationAssignmentRecord.target_kind == ClassificationTargetKind.MUSICAL_WORK.value,
            ClassificationAssignmentRecord.target_id == work_id,
            ClassificationAssignmentRecord.editorial_status == EditorialStatus.PUBLISHED.value,
            ClassificationAssignmentRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        return [assignment_from_record(record) for record in result.scalars()]

    async def list_published_for_recording(self, recording_id: UUID) -> list[ClassificationAssignment]:
        statement = select(ClassificationAssignmentRecord).where(
            ClassificationAssignmentRecord.target_kind == ClassificationTargetKind.RECORDING.value,
            ClassificationAssignmentRecord.target_id == recording_id,
            ClassificationAssignmentRecord.editorial_status == EditorialStatus.PUBLISHED.value,
            ClassificationAssignmentRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        return [assignment_from_record(record) for record in result.scalars()]

    async def list_published_for_recordings(
        self, recording_ids: Collection[UUID]
    ) -> dict[UUID, list[ClassificationAssignment]]:
        ids = set(recording_ids)
        grouped: dict[UUID, list[ClassificationAssignment]] = {recording_id: [] for recording_id in ids}
        if not ids:
            return grouped
        statement = select(ClassificationAssignmentRecord).where(
            ClassificationAssignmentRecord.target_kind == ClassificationTargetKind.RECORDING.value,
            ClassificationAssignmentRecord.target_id.in_(ids),
            ClassificationAssignmentRecord.editorial_status == EditorialStatus.PUBLISHED.value,
            ClassificationAssignmentRecord.deleted.is_(False),
        )
        for record in await self._session.scalars(statement):
            grouped[record.target_id].append(assignment_from_record(record))
        return grouped

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
        await self._flush_unique_constraint()

    async def _flush_unique_constraint(self) -> None:
        try:
            await self._session.flush()
        except IntegrityError as error:
            if (
                isinstance(error.orig, psycopg_errors.UniqueViolation)
                and error.orig.diag.constraint_name == CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT
            ):
                raise UniqueConstraintViolation(CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT) from error
            raise
