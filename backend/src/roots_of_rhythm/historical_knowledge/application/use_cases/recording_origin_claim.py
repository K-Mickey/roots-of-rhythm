from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.historical_knowledge.application.errors import (
    ClaimNotFound,
    EndpointRecordingMissing,
    EndpointRecordingNotPublished,
    EndpointWorkMissing,
    EndpointWorkNotPublished,
    EvidenceFragmentNotReviewed,
)
from roots_of_rhythm.historical_knowledge.application.ports import RecordingOriginClaimRepository, SourceRepository
from roots_of_rhythm.historical_knowledge.domain import (
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    RecordingOriginClaim,
    RecordingOriginPredicate,
)
from roots_of_rhythm.music_catalog.application.ports import MusicalWorkRepository, RecordingRepository

if TYPE_CHECKING:
    from uuid import UUID

type RecordingOriginClaimRepositoryFactory = Callable[[Transaction], RecordingOriginClaimRepository]
type SourceRepositoryFactory = Callable[[Transaction], SourceRepository]
type RecordingRepositoryFactory = Callable[[Transaction], RecordingRepository]
type MusicalWorkRepositoryFactory = Callable[[Transaction], MusicalWorkRepository]


class CreateRecordingOriginClaim:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        claim_repository_factory: RecordingOriginClaimRepositoryFactory,
        recording_repository_factory: RecordingRepositoryFactory,
        work_repository_factory: MusicalWorkRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._claim_repository_factory = claim_repository_factory
        self._recording_repository_factory = recording_repository_factory
        self._work_repository_factory = work_repository_factory

    async def execute(
        self,
        recording_id: UUID,
        work_id: UUID,
        predicate: RecordingOriginPredicate,
        *,
        claim_id: UUID | None = None,
    ) -> RecordingOriginClaim:
        claim = RecordingOriginClaim.create_draft(recording_id, work_id, predicate, claim_id=claim_id)
        async with self._transaction_scope() as transaction:
            if await self._recording_repository_factory(transaction).get(recording_id) is None:
                raise EndpointRecordingMissing(str(recording_id))
            if await self._work_repository_factory(transaction).get(work_id) is None:
                raise EndpointWorkMissing(str(work_id))
            await self._claim_repository_factory(transaction).add(claim)
            await transaction.commit()
            return claim


class PublishRecordingOriginClaim:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        claim_repository_factory: RecordingOriginClaimRepositoryFactory,
        recording_repository_factory: RecordingRepositoryFactory,
        work_repository_factory: MusicalWorkRepositoryFactory,
        source_repository_factory: SourceRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._claim_repository_factory = claim_repository_factory
        self._recording_repository_factory = recording_repository_factory
        self._work_repository_factory = work_repository_factory
        self._source_repository_factory = source_repository_factory

    async def execute(self, claim_id: UUID) -> RecordingOriginClaim:
        async with self._transaction_scope() as transaction:
            claim_repository = self._claim_repository_factory(transaction)
            claim = await claim_repository.get(claim_id, for_update=True)
            if claim is None:
                raise ClaimNotFound(str(claim_id))

            published_recording = await self._recording_repository_factory(transaction).get_published(
                claim.recording_id,
                for_update=True,
            )
            if published_recording is None:
                raise EndpointRecordingNotPublished(str(claim.recording_id))

            if await self._work_repository_factory(transaction).get_published(claim.work_id, for_update=True) is None:
                raise EndpointWorkNotPublished(str(claim.work_id))

            required_role = {
                EvidenceStatus.SUPPORTED: EvidenceRole.SUPPORTS,
                EvidenceStatus.DISPUTED: EvidenceRole.OPPOSES,
            }.get(claim.evidence_status)
            fragment_ids = {
                reference.source_fragment_id
                for reference in claim.evidence_references
                if reference.role is required_role
            }
            fragments = await self._source_repository_factory(transaction).get_fragments_by_ids(
                fragment_ids,
                for_update=True,
            )
            invalid_ids = sorted(
                fragment_id
                for fragment_id in fragment_ids
                if fragment_id not in fragments
                or fragments[fragment_id].review_status is not FragmentReviewStatus.REVIEWED
            )
            if invalid_ids:
                raise EvidenceFragmentNotReviewed(str(invalid_ids[0]))

            published = claim.publish()
            await claim_repository.save(published)
            await transaction.commit()
            return published
