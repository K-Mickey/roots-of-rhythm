from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from types import TracebackType

    from roots_of_rhythm.historical_knowledge.application.ports.claims import (
        ClaimRepository,
        RecordingOriginClaimRepository,
    )
    from roots_of_rhythm.historical_knowledge.application.ports.listening_guides import ListeningGuideRepository
    from roots_of_rhythm.historical_knowledge.application.ports.sources import SourceRepository


class HistoricalKnowledgeUnitOfWork(Protocol):
    claims: ClaimRepository
    recording_origin_claims: RecordingOriginClaimRepository
    listening_guides: ListeningGuideRepository
    sources: SourceRepository

    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
