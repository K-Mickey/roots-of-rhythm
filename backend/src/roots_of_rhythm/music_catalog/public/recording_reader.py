from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import (
        ClassificationAssignment,
        Genre,
        Group,
        MusicalWork,
        Recording,
    )


@dataclass(frozen=True, slots=True)
class RecordingListData:
    recordings: tuple[Recording, ...]
    assignments_by_recording: dict[UUID, tuple[ClassificationAssignment, ...]]
    genres: dict[UUID, Genre]
    groups: dict[UUID, Group]
    person_ids: frozenset[UUID]


@dataclass(frozen=True, slots=True)
class RecordingOverviewData:
    recording: Recording | None
    works: dict[UUID, MusicalWork]
    assignments: tuple[ClassificationAssignment, ...]
    genres: dict[UUID, Genre]
    groups: dict[UUID, Group]
    person_ids: frozenset[UUID]


class RecordingReader(Protocol):
    async def list_overview(self) -> RecordingListData: ...

    async def get_recording_overview(self, recording_id: UUID) -> RecordingOverviewData: ...
