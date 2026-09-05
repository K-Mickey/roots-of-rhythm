from asyncio import gather
from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.historical_knowledge.application.ports import (
    ListeningGuideRepository,
    RecordingOriginClaimRepository,
    SourceRepository,
)
from roots_of_rhythm.historical_knowledge.public.recording_knowledge_reader import (
    RecordingKnowledgeData,
)

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import (
        ListeningGuide,
        RecordingOriginClaim,
        SourceAccessPolicy,
    )

type ListeningGuideRepositoryFactory = Callable[[Transaction], ListeningGuideRepository]
type RecordingOriginClaimRepositoryFactory = Callable[[Transaction], RecordingOriginClaimRepository]
type SourceRepositoryFactory = Callable[[Transaction], SourceRepository]


class RecordingKnowledgeReadService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        listening_guide_repository_factory: ListeningGuideRepositoryFactory,
        recording_origin_claim_repository_factory: RecordingOriginClaimRepositoryFactory,
        source_repository_factory: SourceRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._listening_guide_repository_factory = listening_guide_repository_factory
        self._recording_origin_claim_repository_factory = recording_origin_claim_repository_factory
        self._source_repository_factory = source_repository_factory

    async def get_recording_data(
        self,
        recording_id: UUID,
        source_version_ids: Collection[UUID],
    ) -> RecordingKnowledgeData:
        guide, origin_claims, source_access_by_version = await gather(
            self._load_listening_guide(recording_id),
            self._load_origin_claims(recording_id),
            self._load_source_access(source_version_ids),
        )
        return RecordingKnowledgeData(
            listening_guide=guide,
            origin_claims=origin_claims,
            source_access_by_version=source_access_by_version,
        )

    async def _load_listening_guide(self, recording_id: UUID) -> ListeningGuide | None:
        async with self._transaction_scope() as transaction:
            listening_guide_repository = self._listening_guide_repository_factory(transaction)
            return await listening_guide_repository.get_published_for_recording(recording_id)

    async def _load_origin_claims(self, recording_id: UUID) -> tuple[RecordingOriginClaim, ...]:
        async with self._transaction_scope() as transaction:
            origin_claim_repository = self._recording_origin_claim_repository_factory(transaction)
            claims_by_recording = await origin_claim_repository.list_supported_published_for_recordings([recording_id])
        return tuple(claims_by_recording.get(recording_id, ()))

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
