from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.historical_knowledge.application.errors import (
    ClaimNotFound,
    EndpointGenreMissing,
    EndpointGenreNotPublished,
    EvidenceFragmentNotReviewed,
)
from roots_of_rhythm.historical_knowledge.application.ports import ClaimRepository, SourceRepository
from roots_of_rhythm.historical_knowledge.domain import (
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    GenreRelationClaim,
    RelationType,
)
from roots_of_rhythm.music_catalog.application.ports import GenreRepository

if TYPE_CHECKING:
    from uuid import UUID

type ClaimRepositoryFactory = Callable[[Transaction], ClaimRepository]
type SourceRepositoryFactory = Callable[[Transaction], SourceRepository]
type GenreRepositoryFactory = Callable[[Transaction], GenreRepository]


class CreateGenreRelationClaim:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        claim_repository_factory: ClaimRepositoryFactory,
        genre_repository_factory: GenreRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._claim_repository_factory = claim_repository_factory
        self._genre_repository_factory = genre_repository_factory

    async def execute(
        self,
        subject_genre_id: UUID,
        target_genre_id: UUID,
        relation_type: RelationType,
        *,
        claim_id: UUID | None = None,
    ) -> GenreRelationClaim:
        claim = GenreRelationClaim.create_draft(
            subject_genre_id,
            target_genre_id,
            relation_type,
            claim_id=claim_id,
        )
        async with self._transaction_scope() as transaction:
            genre_ids = {subject_genre_id, target_genre_id}
            genres = await self._genre_repository_factory(transaction).get_by_ids(genre_ids)
            missing_ids = sorted(genre_ids - genres.keys())
            if missing_ids:
                raise EndpointGenreMissing(str(missing_ids[0]))
            await self._claim_repository_factory(transaction).add(claim)
            await transaction.commit()
            return claim


class PublishGenreRelationClaim:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        claim_repository_factory: ClaimRepositoryFactory,
        source_repository_factory: SourceRepositoryFactory,
        genre_repository_factory: GenreRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._claim_repository_factory = claim_repository_factory
        self._source_repository_factory = source_repository_factory
        self._genre_repository_factory = genre_repository_factory

    async def execute(self, claim_id: UUID) -> GenreRelationClaim:
        async with self._transaction_scope() as transaction:
            claim_repository = self._claim_repository_factory(transaction)
            claim = await claim_repository.get(claim_id, for_update=True)
            if claim is None:
                raise ClaimNotFound(str(claim_id))

            genre_ids = {claim.subject_genre_id, claim.target_genre_id}
            genres = await self._genre_repository_factory(transaction).get_published_by_ids(
                genre_ids,
                for_update=True,
            )
            missing_ids = sorted(genre_ids - genres.keys())
            if missing_ids:
                raise EndpointGenreNotPublished(str(missing_ids[0]))

            required_role = {
                EvidenceStatus.SUPPORTED: EvidenceRole.SUPPORTS,
                EvidenceStatus.DISPUTED: EvidenceRole.OPPOSES,
            }.get(claim.evidence_status)
            fragment_ids = {
                reference.source_fragment_id
                for reference in claim.evidence_references
                if reference.role is required_role
            }
            if fragment_ids:
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
