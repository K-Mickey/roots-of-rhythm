from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import RecordingOriginClaim, SourceAccessPolicy


@dataclass(frozen=True, slots=True)
class SongHistoricalKnowledgeReadData:
    source_access_by_version: tuple[tuple[UUID, SourceAccessPolicy], ...]
    origin_claims: tuple[RecordingOriginClaim, ...]


class SongHistoricalKnowledgeReader(Protocol):
    async def get_song_data(
        self,
        source_version_ids: Collection[UUID],
        recording_ids: Collection[UUID],
    ) -> SongHistoricalKnowledgeReadData: ...
