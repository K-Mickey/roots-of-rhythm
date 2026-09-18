from typing import TYPE_CHECKING, Self

from sqlalchemy.exc import IntegrityError

from roots_of_rhythm.historical_knowledge.infrastructure.repositories.claim import SqlAlchemyClaimRepository
from roots_of_rhythm.historical_knowledge.infrastructure.repositories.listening_guide import (
    SqlAlchemyListeningGuideRepository,
)
from roots_of_rhythm.historical_knowledge.infrastructure.repositories.recording_origin_claim import (
    SqlAlchemyRecordingOriginClaimRepository,
)
from roots_of_rhythm.historical_knowledge.infrastructure.repositories.source import SqlAlchemySourceRepository

if TYPE_CHECKING:
    from types import TracebackType

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from roots_of_rhythm.historical_knowledge.application.ports import (
        ClaimRepository,
        ListeningGuideRepository,
        RecordingOriginClaimRepository,
        SourceRepository,
    )


class SqlAlchemyHistoricalKnowledgeUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session = session_factory()
        self.claims: ClaimRepository = SqlAlchemyClaimRepository(self._session)
        self.recording_origin_claims: RecordingOriginClaimRepository = SqlAlchemyRecordingOriginClaimRepository(
            self._session
        )
        self.listening_guides: ListeningGuideRepository = SqlAlchemyListeningGuideRepository(self._session)
        self.sources: SourceRepository = SqlAlchemySourceRepository(self._session)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        try:
            await self._session.commit()
        except IntegrityError:
            await self.rollback()
            raise

    async def rollback(self) -> None:
        await self._session.rollback()
