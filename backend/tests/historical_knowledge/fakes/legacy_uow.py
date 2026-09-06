from typing import TYPE_CHECKING, Self

from tests.historical_knowledge.fakes.claims import FakeClaimRepository
from tests.historical_knowledge.fakes.listening_guides import StubListeningGuideRepository
from tests.historical_knowledge.fakes.origin_claims import StubRecordingOriginClaimRepository

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.application.ports import (
        ClaimRepository,
        ListeningGuideRepository,
        RecordingOriginClaimRepository,
        SourceRepository,
    )
    from roots_of_rhythm.historical_knowledge.domain import GenreRelationClaim
    from tests.historical_knowledge.fakes.sources import FakeSourceRepository


class FakeHistoricalKnowledgeUnitOfWork:
    def __init__(self, claims: dict[UUID, GenreRelationClaim], sources: "FakeSourceRepository") -> None:
        self.claims: ClaimRepository = FakeClaimRepository(claims)
        self.recording_origin_claims: RecordingOriginClaimRepository = StubRecordingOriginClaimRepository()
        self.listening_guides: ListeningGuideRepository = StubListeningGuideRepository()
        self.sources: SourceRepository = sources
        self.commits = 0
        self.enter_count = 0

    async def __aenter__(self) -> Self:
        self.enter_count += 1
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        return None
