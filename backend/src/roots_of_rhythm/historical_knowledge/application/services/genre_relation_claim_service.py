from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.historical_knowledge.application.errors import ClaimNotFound, SourceNotFound
from roots_of_rhythm.historical_knowledge.application.ports import ClaimRepository, SourceRepository

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import (
        ClaimEvidenceReference,
        ClaimProvenance,
        EvidenceStatus,
        GenreRelationClaim,
        GeographicContext,
        HistoricalPeriod,
        RelationType,
    )

type ClaimRepositoryFactory = Callable[[Transaction], ClaimRepository]
type SourceRepositoryFactory = Callable[[Transaction], SourceRepository]


class GenreRelationClaimService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        claim_repository_factory: ClaimRepositoryFactory,
        source_repository_factory: SourceRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._claim_repository_factory = claim_repository_factory
        self._source_repository_factory = source_repository_factory

    async def replace_content(
        self,
        claim_id: UUID,
        *,
        relation_type: RelationType | None = None,
        explanation: str | None = None,
        temporal: HistoricalPeriod | None = None,
        geographic: GeographicContext | None = None,
        provenance: ClaimProvenance | None = None,
        evidence_status: EvidenceStatus | None = None,
    ) -> GenreRelationClaim:
        async with self._transaction_scope() as transaction:
            claim_repository = self._claim_repository_factory(transaction)
            claim = await _get_claim(claim_repository, claim_id, for_update=True)
            updated = claim.replace_content(
                relation_type=relation_type,
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
    ) -> GenreRelationClaim:
        async with self._transaction_scope() as transaction:
            claim_repository = self._claim_repository_factory(transaction)
            claim = await _get_claim(claim_repository, claim_id, for_update=True)
            fragment_ids = {reference.source_fragment_id for reference in references}
            source_repository = self._source_repository_factory(transaction)
            fragments = await source_repository.get_fragments_by_ids(fragment_ids, for_update=True)
            missing_ids = sorted(fragment_ids - fragments.keys())
            if missing_ids:
                raise SourceNotFound(str(missing_ids[0]))
            updated = claim.replace_evidence(references)
            await claim_repository.save(updated)
            await transaction.commit()
            return updated

    async def archive(self, claim_id: UUID) -> GenreRelationClaim:
        async with self._transaction_scope() as transaction:
            claim_repository = self._claim_repository_factory(transaction)
            claim = await _get_claim(claim_repository, claim_id, for_update=True)
            archived = claim.archive()
            await claim_repository.save(archived)
            await transaction.commit()
            return archived


async def _get_claim(
    claim_repository: ClaimRepository,
    claim_id: UUID,
    *,
    for_update: bool = False,
) -> GenreRelationClaim:
    claim = await claim_repository.get(claim_id, for_update=for_update)
    if claim is None:
        raise ClaimNotFound(str(claim_id))
    return claim
