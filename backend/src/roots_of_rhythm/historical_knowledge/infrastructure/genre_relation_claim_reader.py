from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.domain import EditorialStatus
from roots_of_rhythm.historical_knowledge.infrastructure.claim_repository import SqlAlchemyClaimRepository
from roots_of_rhythm.historical_knowledge.infrastructure.source_repository import SqlAlchemySourceRepository
from roots_of_rhythm.historical_knowledge.public.genre_relation_claim_reader import (
    PublicEvidenceReference,
    PublishedGenreRelationClaims,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SqlAlchemyPublishedGenreRelationClaimReader:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def read_for_genre(self, genre_id: UUID) -> PublishedGenreRelationClaims:
        async with self._session_factory() as session:
            claim_repository = SqlAlchemyClaimRepository(session)
            source_repository = SqlAlchemySourceRepository(session)
            claims = tuple(
                claim
                for claim in await claim_repository.list_by_genre(genre_id)
                if claim.editorial_status is EditorialStatus.PUBLISHED
            )
            fragment_ids = {reference.source_fragment_id for claim in claims for reference in claim.evidence_references}
            source_ids = await source_repository.reviewed_source_ids_for_fragments(fragment_ids)

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
