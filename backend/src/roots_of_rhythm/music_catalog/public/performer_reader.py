from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import ClassificationAssignment, Genre


@dataclass(frozen=True, slots=True)
class PerformerData:
    assignments: tuple[ClassificationAssignment, ...]
    genres: dict[UUID, Genre]


class PerformerReader(Protocol):
    async def get_performer_data(self, person_id: UUID) -> PerformerData: ...
