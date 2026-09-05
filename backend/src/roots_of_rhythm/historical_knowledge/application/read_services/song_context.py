from asyncio import gather
from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.historical_knowledge.application.ports import (
    RecordingOriginClaimRepository,
    SourceRepository,
)
from roots_of_rhythm.historical_knowledge.public.song_context_reader import (
    SongHistoricalKnowledgeReadData,
)

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import RecordingOriginClaim, SourceAccessPolicy

type RecordingOriginClaimRepositoryFactory = Callable[[Transaction], RecordingOriginClaimRepository]
type SourceRepositoryFactory = Callable[[Transaction], SourceRepository]


class SongContextReadService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        recording_origin_claim_repository_factory: RecordingOriginClaimRepositoryFactory,
        source_repository_factory: SourceRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._recording_origin_claim_repository_factory = recording_origin_claim_repository_factory
        self._source_repository_factory = source_repository_factory

    async def get_song_data(
        self,
        source_version_ids: Collection[UUID],
        recording_ids: Collection[UUID],
    ) -> SongHistoricalKnowledgeReadData:
        source_access_by_version, claims = await gather(
            self._load_source_access(source_version_ids),
            self._load_claims(recording_ids),
        )
        return SongHistoricalKnowledgeReadData(source_access_by_version, claims)

    async def _load_source_access(
        self,
        source_version_ids: Collection[UUID],
    ) -> tuple[tuple[UUID, SourceAccessPolicy], ...]:
        if not source_version_ids:
            return ()
        async with self._transaction_scope() as transaction:
            sources_repository = self._source_repository_factory(transaction)
            versions = await sources_repository.get_versions_by_ids(source_version_ids)
            source_ids = {item.source_id for item in versions.values()}
            sources = {}
            if source_ids:
                sources = await sources_repository.get_sources_by_ids(source_ids)
        return tuple(
            (version_id, source.access_policy)
            for version_id, version in versions.items()
            if (source := sources.get(version.source_id)) is not None
        )

    async def _load_claims(self, recording_ids: Collection[UUID]) -> tuple[RecordingOriginClaim, ...]:
        if not recording_ids:
            return ()
        async with self._transaction_scope() as transaction:
            claims_repository = self._recording_origin_claim_repository_factory(transaction)
            claims = await claims_repository.list_supported_published_for_recordings(recording_ids)
        return tuple(item for items in claims.values() for item in items)
