from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.public import PublicEvidenceReference, PublishedGenreRelationClaims

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import GenreRelationClaim
    from tests.historical_knowledge.fakes.sources import FakeSourceRepository


class FakeClaimRepository:
    def __init__(self, claims: dict[UUID, GenreRelationClaim]) -> None:
        self._claims = claims

    async def add(self, claim: GenreRelationClaim) -> None:
        self._claims[claim.id] = claim

    async def get(self, claim_id: UUID, *, for_update: bool = False) -> GenreRelationClaim | None:
        return self._claims.get(claim_id)

    async def save(self, claim: GenreRelationClaim) -> None:
        self._claims[claim.id] = claim

    async def mark_deleted(self, claim_id: UUID) -> None:
        self._claims.pop(claim_id, None)

    async def list_by_genre(self, genre_id: UUID) -> list[GenreRelationClaim]:
        return [
            claim
            for claim in self._claims.values()
            if claim.subject_genre_id == genre_id or claim.target_genre_id == genre_id
        ]


class FakePublishedGenreRelationClaimReader:
    def __init__(self, claims: dict[UUID, GenreRelationClaim], sources: "FakeSourceRepository") -> None:
        self._claims = claims
        self._sources = sources

    async def read_for_genre(self, genre_id: UUID) -> PublishedGenreRelationClaims:
        claims = tuple(
            claim
            for claim in self._claims.values()
            if claim.is_published and (claim.subject_genre_id == genre_id or claim.target_genre_id == genre_id)
        )
        source_ids = await self._sources.reviewed_source_ids_for_fragments(
            {reference.source_fragment_id for claim in claims for reference in claim.evidence_references}
        )
        return PublishedGenreRelationClaims(
            claims,
            {
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
