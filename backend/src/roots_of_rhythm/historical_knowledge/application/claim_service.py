from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
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
from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork

if TYPE_CHECKING:
    from uuid import UUID

type KnowledgeMusicScopeFactory = Callable[
    [],
    AbstractAsyncContextManager[tuple[HistoricalKnowledgeUnitOfWork, MusicCatalogUnitOfWork]],
]


@dataclass(frozen=True, slots=True)
class PublicEvidenceReference:
    source_id: UUID
    role: EvidenceRole
    locator_text: str | None
    external_url: str | None


class ClaimService:
    def __init__(self, catalogs: KnowledgeMusicScopeFactory) -> None:
        self._catalogs = catalogs

    async def create_draft(
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
        async with self._catalogs() as (hk, music):
            await self._ensure_genres_exist(music, subject_genre_id, target_genre_id)
            await hk.claims.add(claim)
            await hk.commit()
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
        async with self._catalogs() as (hk, _music):
            claim = await self._get(hk, claim_id, for_update=True)
            updated = claim.replace_content(
                relation_type=relation_type,
                explanation=explanation,
                temporal=temporal,
                geographic=geographic,
                provenance=provenance,
                evidence_status=evidence_status,
            )
            await hk.claims.save(updated)
            await hk.commit()
            return updated

    async def replace_evidence(
        self,
        claim_id: UUID,
        references: tuple[ClaimEvidenceReference, ...],
    ) -> GenreRelationClaim:
        async with self._catalogs() as (hk, _music):
            claim = await self._get(hk, claim_id, for_update=True)
            for fragment_id in sorted({reference.source_fragment_id for reference in references}):
                if await hk.sources.get_fragment(fragment_id, for_update=True) is None:
                    raise SourceNotFound(str(fragment_id))
            updated = claim.replace_evidence(references)
            await hk.claims.save(updated)
            await hk.commit()
            return updated

    async def publish(self, claim_id: UUID) -> GenreRelationClaim:
        async with self._catalogs() as (hk, music):
            claim = await self._get(hk, claim_id, for_update=True)
            await self._ensure_endpoints_published(music, claim.subject_genre_id, claim.target_genre_id)
            await self._ensure_evidence_fragments_reviewed(hk, claim)
            published = claim.publish()
            await hk.claims.save(published)
            await hk.commit()
            return published

    async def archive(self, claim_id: UUID) -> GenreRelationClaim:
        async with self._catalogs() as (hk, _music):
            claim = await self._get(hk, claim_id, for_update=True)
            archived = claim.archive()
            await hk.claims.save(archived)
            await hk.commit()
            return archived

    async def get_publicly_visible(self, claim_id: UUID) -> GenreRelationClaim | None:
        async with self._catalogs() as (hk, music):
            claim = await hk.claims.get(claim_id)
            if claim is None:
                return None
            if not await self._is_visible(music, claim):
                return None
            return claim

    async def list_public_for_genre(self, genre_id: UUID) -> list[GenreRelationClaim]:
        async with self._catalogs() as (hk, music):
            claims = await hk.claims.list_by_genre(genre_id)
            endpoint_ids = {claim.subject_genre_id for claim in claims} | {claim.target_genre_id for claim in claims}
            published = await music.genres.published_among(endpoint_ids)
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
        async with self._catalogs() as (hk, _music):
            public_refs: list[ClaimEvidenceReference] = []
            for reference in claim.evidence_references:
                fragment = await hk.sources.get_fragment(reference.source_fragment_id)
                if fragment is not None and fragment.review_status is FragmentReviewStatus.REVIEWED:
                    public_refs.append(reference)
            return tuple(public_refs)

    async def public_evidence_references_for_claims(
        self,
        claims: Sequence[GenreRelationClaim],
    ) -> dict[UUID, tuple[PublicEvidenceReference, ...]]:
        fragment_ids = {reference.source_fragment_id for claim in claims for reference in claim.evidence_references}
        async with self._catalogs() as (hk, _music):
            source_ids = await hk.sources.reviewed_source_ids_for_fragments(fragment_ids)
        result: dict[UUID, tuple[PublicEvidenceReference, ...]] = {}
        for claim in claims:
            references: list[PublicEvidenceReference] = []
            for reference in claim.evidence_references:
                source_id = source_ids.get(reference.source_fragment_id)
                if source_id is None:
                    continue
                references.append(
                    PublicEvidenceReference(
                        source_id=source_id,
                        role=reference.role,
                        locator_text=reference.locator_text,
                        external_url=reference.external_url,
                    )
                )
            result[claim.id] = tuple(references)
        return result

    @staticmethod
    async def _is_visible(music: MusicCatalogUnitOfWork, claim: GenreRelationClaim) -> bool:
        published = await music.genres.published_among({claim.subject_genre_id, claim.target_genre_id})
        return is_claim_publicly_visible(
            claim,
            subject_published=claim.subject_genre_id in published,
            target_published=claim.target_genre_id in published,
        )

    @staticmethod
    async def _ensure_genres_exist(
        music: MusicCatalogUnitOfWork,
        subject_genre_id: UUID,
        target_genre_id: UUID,
    ) -> None:
        if await music.genres.get(subject_genre_id) is None:
            raise EndpointGenreMissing(str(subject_genre_id))
        if await music.genres.get(target_genre_id) is None:
            raise EndpointGenreMissing(str(target_genre_id))

    @staticmethod
    async def _ensure_endpoints_published(
        music: MusicCatalogUnitOfWork,
        subject_genre_id: UUID,
        target_genre_id: UUID,
    ) -> None:
        for genre_id in sorted((subject_genre_id, target_genre_id)):
            if await music.genres.get_published(genre_id, for_update=True) is None:
                raise EndpointGenreNotPublished(str(genre_id))

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
        fragment_ids = sorted(
            {reference.source_fragment_id for reference in claim.evidence_references if reference.role is required_role}
        )
        for fragment_id in fragment_ids:
            fragment = await uow.sources.get_fragment(fragment_id, for_update=True)
            if fragment is None or fragment.review_status is not FragmentReviewStatus.REVIEWED:
                raise EvidenceFragmentNotReviewed(str(fragment_id))

    @staticmethod
    async def _get(
        uow: HistoricalKnowledgeUnitOfWork,
        claim_id: UUID,
        *,
        for_update: bool = False,
    ) -> GenreRelationClaim:
        claim = await uow.claims.get(claim_id, for_update=for_update)
        if claim is None:
            raise ClaimNotFound(str(claim_id))
        return claim
