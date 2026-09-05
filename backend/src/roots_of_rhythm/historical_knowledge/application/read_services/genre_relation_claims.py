from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.historical_knowledge.application.ports import ClaimRepository, SourceRepository
from roots_of_rhythm.historical_knowledge.public.genre_relation_claim_reader import (
    PublicEvidenceReference,
    PublishedGenreRelationClaims,
)

if TYPE_CHECKING:
    from uuid import UUID

type ClaimRepositoryFactory = Callable[[Transaction], ClaimRepository]
type SourceRepositoryFactory = Callable[[Transaction], SourceRepository]


class GenreRelationClaimReadService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        claim_repository_factory: ClaimRepositoryFactory,
        source_repository_factory: SourceRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._claim_repository_factory = claim_repository_factory
        self._source_repository_factory = source_repository_factory

    async def read_for_genre(self, genre_id: UUID) -> PublishedGenreRelationClaims:
        async with self._transaction_scope() as transaction:
            claim_repository = self._claim_repository_factory(transaction)
            claims = tuple(claim for claim in await claim_repository.list_by_genre(genre_id) if claim.is_published)
            fragment_ids = {reference.source_fragment_id for claim in claims for reference in claim.evidence_references}
            source_ids = await self._source_repository_factory(transaction).reviewed_source_ids_for_fragments(
                fragment_ids
            )

        return PublishedGenreRelationClaims(
            claims=claims,
            evidence_by_claim={
                claim.id: tuple(
                    PublicEvidenceReference(
                        source_id=source_id,
                        role=reference.role,
                        locator_text=reference.locator_text,
                        external_url=reference.external_url,
                    )
                    for reference in claim.evidence_references
                    if (source_id := source_ids.get(reference.source_fragment_id)) is not None
                )
                for claim in claims
            },
        )
