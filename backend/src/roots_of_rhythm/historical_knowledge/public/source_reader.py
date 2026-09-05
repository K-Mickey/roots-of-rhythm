from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import Source


class SourceReader(Protocol):
    async def get_sources_by_ids(self, source_ids: Collection[UUID]) -> dict[UUID, Source]: ...
