from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import ClassificationAssignment


class FakeClassificationAssignmentRepository:
    def __init__(self, assignments: dict[UUID, ClassificationAssignment]) -> None:
        self._assignments = assignments

    async def add(self, assignment: ClassificationAssignment) -> None:
        self._assignments[assignment.id] = assignment

    async def get(self, assignment_id: UUID, *, for_update: bool = False) -> ClassificationAssignment | None:
        return self._assignments.get(assignment_id)

    async def list_published_for_person(self, person_id: UUID) -> list[ClassificationAssignment]:
        return [
            assignment
            for assignment in self._assignments.values()
            if assignment.is_person_target and assignment.target_id == person_id and assignment.is_published
        ]

    async def list_published_for_group(self, group_id: UUID) -> list[ClassificationAssignment]:
        return [
            assignment
            for assignment in self._assignments.values()
            if assignment.is_group_target and assignment.target_id == group_id and assignment.is_published
        ]

    async def list_published_for_work(self, work_id: UUID) -> list[ClassificationAssignment]:
        return [
            assignment
            for assignment in self._assignments.values()
            if assignment.is_music_work_target and assignment.target_id == work_id and assignment.is_published
        ]

    async def list_published_for_recording(self, recording_id: UUID) -> list[ClassificationAssignment]:
        return [
            assignment
            for assignment in self._assignments.values()
            if assignment.is_recording_target and assignment.target_id == recording_id and assignment.is_published
        ]

    async def list_published_for_recordings(
        self, recording_ids: Collection[UUID]
    ) -> dict[UUID, list[ClassificationAssignment]]:
        return {recording_id: await self.list_published_for_recording(recording_id) for recording_id in recording_ids}

    async def save(self, assignment: ClassificationAssignment) -> None:
        if assignment.id not in self._assignments:
            raise LookupError(str(assignment.id))
        self._assignments[assignment.id] = assignment
