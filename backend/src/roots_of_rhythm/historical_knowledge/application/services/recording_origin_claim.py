from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.historical_knowledge.application.errors import (
    ClaimNotFound,
    SourceNotFound,
)
from roots_of_rhythm.historical_knowledge.application.ports import RecordingOriginClaimRepository, SourceRepository

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import (
        ClaimEvidenceReference,
        ClaimProvenance,
        EvidenceStatus,
        GeographicContext,
        HistoricalPeriod,
        RecordingOriginClaim,
    )

type RecordingOriginClaimRepositoryFactory = Callable[[Transaction], RecordingOriginClaimRepository]
type SourceRepositoryFactory = Callable[[Transaction], SourceRepository]


class RecordingOriginClaimService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        claim_repository_factory: RecordingOriginClaimRepositoryFactory,
        source_repository_factory: SourceRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._claim_repository_factory = claim_repository_factory
        self._source_repository_factory = source_repository_factory

    async def replace_content(
        self,
        claim_id: UUID,
        *,
        explanation: str | None = None,
        temporal: HistoricalPeriod | None = None,
        geographic: GeographicContext | None = None,
        provenance: ClaimProvenance | None = None,
        evidence_status: EvidenceStatus | None = None,
    ) -> RecordingOriginClaim:
        async with self._transaction_scope() as transaction:
            claim_repository = self._claim_repository_factory(transaction)
            claim = await _get_claim(claim_repository, claim_id)
            updated = claim.replace_content(
                explanation=explanation,
                temporal=temporal,
                geographic=geographic,
                provenance=provenance,
                evidence_status=evidence_status,
            )
            await claim_repository.save(updated)
            await transaction.commit()
            return updated

    async def replace_evidence(
        self,
        claim_id: UUID,
        references: tuple[ClaimEvidenceReference, ...],
    ) -> RecordingOriginClaim:
        async with self._transaction_scope() as transaction:
            claim_repository = self._claim_repository_factory(transaction)
            claim = await _get_claim(claim_repository, claim_id)
            fragment_ids = {reference.source_fragment_id for reference in references}
            fragments = await self._source_repository_factory(transaction).get_fragments_by_ids(
                fragment_ids,
                for_update=True,
            )
            missing_ids = sorted(fragment_ids - fragments.keys())
            if missing_ids:
                raise SourceNotFound(str(missing_ids[0]))
            updated = claim.replace_evidence(references)
            await claim_repository.save(updated)
            await transaction.commit()
            return updated

    async def archive(self, claim_id: UUID) -> RecordingOriginClaim:
        async with self._transaction_scope() as transaction:
            claim_repository = self._claim_repository_factory(transaction)
            claim = await _get_claim(claim_repository, claim_id)
            archived = claim.archive()
            await claim_repository.save(archived)
            await transaction.commit()
            return archived


async def _get_claim(
    repository: RecordingOriginClaimRepository,
    claim_id: UUID,
) -> RecordingOriginClaim:
    claim = await repository.get(claim_id, for_update=True)
    if claim is None:
        raise ClaimNotFound(str(claim_id))
    return claim
