from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import ListeningGuide, RecordingOriginClaim, SourceAccessPolicy


@dataclass(frozen=True, slots=True)
class RecordingKnowledgeData:
    listening_guide: ListeningGuide | None
    origin_claims: tuple[RecordingOriginClaim, ...]
    source_access_by_version: tuple[tuple[UUID, SourceAccessPolicy], ...]


class RecordingKnowledgeReader(Protocol):
    async def get_recording_data(
        self,
        recording_id: UUID,
        source_version_ids: Collection[UUID],
    ) -> RecordingKnowledgeData: ...
