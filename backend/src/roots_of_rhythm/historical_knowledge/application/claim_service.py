from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.application.errors import (
    ClaimNotFound,
    EndpointGenreMissing,
    EndpointGenreNotPublished,
    EvidenceFragmentNotReviewed,
    SourceNotFound,
)
from roots_of_rhythm.historical_knowledge.application.ports import HistoricalKnowledgeUnitOfWork
from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    GenreRelationClaim,
    GeographicContext,
    HistoricalPeriod,
    RelationType,
    is_claim_publicly_visible,
)

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.application.ports import GenreStatusLookup

type UnitOfWorkFactory = Callable[[], HistoricalKnowledgeUnitOfWork]


class ClaimService:
    def __init__(self, uow_factory: UnitOfWorkFactory, genre_status: GenreStatusLookup) -> None:
        self._uow_factory = uow_factory
        self._genre_status = genre_status

    async def create_draft(
        self,
        subject_genre_id: UUID,
        target_genre_id: UUID,
        relation_type: RelationType,
        *,
        claim_id: UUID | None = None,
    ) -> GenreRelationClaim:
        await self._ensure_genres_exist(subject_genre_id, target_genre_id)
        claim = GenreRelationClaim.create_draft(
            subject_genre_id,
            target_genre_id,
            relation_type,
            claim_id=claim_id,
        )
        async with self._uow_factory() as uow:
            await uow.claims.add(claim)
            await uow.commit()
            return claim

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
        async with self._uow_factory() as uow:
            claim = await self._get(uow, claim_id)
            updated = claim.replace_content(
                relation_type=relation_type,
                explanation=explanation,
                temporal=temporal,
                geographic=geographic,
                provenance=provenance,
                evidence_status=evidence_status,
            )
            await uow.claims.save(updated)
            await uow.commit()
            return updated

    async def replace_evidence(
        self,
        claim_id: UUID,
        references: tuple[ClaimEvidenceReference, ...],
    ) -> GenreRelationClaim:
        async with self._uow_factory() as uow:
            claim = await self._get(uow, claim_id)
            for reference in references:
                fragment = await uow.sources.get_fragment(reference.source_fragment_id)
                if fragment is None:
                    raise SourceNotFound(str(reference.source_fragment_id))
            updated = claim.replace_evidence(references)
            await uow.claims.save(updated)
            await uow.commit()
            return updated

    async def publish(self, claim_id: UUID) -> GenreRelationClaim:
        async with self._uow_factory() as uow:
            claim = await self._get(uow, claim_id)
            await self._ensure_endpoints_published(claim.subject_genre_id, claim.target_genre_id)
            await self._ensure_evidence_fragments_reviewed(uow, claim)
            published = claim.publish()
            await uow.claims.save(published)
            await uow.commit()
            return published

    async def archive(self, claim_id: UUID) -> GenreRelationClaim:
        async with self._uow_factory() as uow:
            claim = await self._get(uow, claim_id)
            archived = claim.archive()
            await uow.claims.save(archived)
            await uow.commit()
            return archived

    async def get_publicly_visible(self, claim_id: UUID) -> GenreRelationClaim | None:
        async with self._uow_factory() as uow:
            claim = await uow.claims.get(claim_id)
            if claim is None:
                return None
            if not await self._is_visible(claim):
                return None
            return claim

    async def list_public_for_genre(self, genre_id: UUID) -> list[GenreRelationClaim]:
        async with self._uow_factory() as uow:
            claims = await uow.claims.list_by_genre(genre_id)
        endpoint_ids = {claim.subject_genre_id for claim in claims} | {claim.target_genre_id for claim in claims}
        published = await self._genre_status.published_among(endpoint_ids)
        return [
            claim
            for claim in claims
            if is_claim_publicly_visible(
                claim,
                subject_published=claim.subject_genre_id in published,
                target_published=claim.target_genre_id in published,
            )
        ]

    async def public_evidence_references(self, claim: GenreRelationClaim) -> tuple[ClaimEvidenceReference, ...]:
        async with self._uow_factory() as uow:
            public_refs: list[ClaimEvidenceReference] = []
            for reference in claim.evidence_references:
                fragment = await uow.sources.get_fragment(reference.source_fragment_id)
                if fragment is not None and fragment.review_status is FragmentReviewStatus.REVIEWED:
                    public_refs.append(reference)
            return tuple(public_refs)

    async def _is_visible(self, claim: GenreRelationClaim) -> bool:
        published = await self._genre_status.published_among({claim.subject_genre_id, claim.target_genre_id})
        return is_claim_publicly_visible(
            claim,
            subject_published=claim.subject_genre_id in published,
            target_published=claim.target_genre_id in published,
        )

    async def _ensure_genres_exist(self, subject_genre_id: UUID, target_genre_id: UUID) -> None:
        if not await self._genre_status.exists(subject_genre_id):
            raise EndpointGenreMissing(str(subject_genre_id))
        if not await self._genre_status.exists(target_genre_id):
            raise EndpointGenreMissing(str(target_genre_id))

    async def _ensure_endpoints_published(self, subject_genre_id: UUID, target_genre_id: UUID) -> None:
        if not await self._genre_status.is_published(subject_genre_id):
            raise EndpointGenreNotPublished(str(subject_genre_id))
        if not await self._genre_status.is_published(target_genre_id):
            raise EndpointGenreNotPublished(str(target_genre_id))

    @staticmethod
    async def _ensure_evidence_fragments_reviewed(
        uow: HistoricalKnowledgeUnitOfWork,
        claim: GenreRelationClaim,
    ) -> None:
        if claim.evidence_status is EvidenceStatus.UNVERIFIED:
            return
        required_roles = {
            EvidenceStatus.SUPPORTED: EvidenceRole.SUPPORTS,
            EvidenceStatus.DISPUTED: EvidenceRole.OPPOSES,
        }
        required_role = required_roles[claim.evidence_status]
        for reference in claim.evidence_references:
            if reference.role is not required_role:
                continue
            fragment = await uow.sources.get_fragment(reference.source_fragment_id)
            if fragment is None or fragment.review_status is not FragmentReviewStatus.REVIEWED:
                raise EvidenceFragmentNotReviewed(str(reference.source_fragment_id))

    @staticmethod
    async def _get(uow: HistoricalKnowledgeUnitOfWork, claim_id: UUID) -> GenreRelationClaim:
        claim = await uow.claims.get(claim_id)
        if claim is None:
            raise ClaimNotFound(str(claim_id))
        return claim
