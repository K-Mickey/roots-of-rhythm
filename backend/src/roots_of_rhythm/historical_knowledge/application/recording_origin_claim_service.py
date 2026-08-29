from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.application.errors import (
    ClaimNotFound,
    EndpointRecordingMissing,
    EndpointRecordingNotPublished,
    EndpointWorkMissing,
    EndpointWorkNotPublished,
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
    GeographicContext,
    HistoricalPeriod,
    RecordingOriginClaim,
    RecordingOriginPredicate,
)
from roots_of_rhythm.music_catalog.application.ports import RecordingUnitOfWork

if TYPE_CHECKING:
    from uuid import UUID

type KnowledgeRecordingScopeFactory = Callable[
    [],
    AbstractAsyncContextManager[tuple[HistoricalKnowledgeUnitOfWork, RecordingUnitOfWork]],
]


class RecordingOriginClaimService:
    def __init__(self, catalogs: KnowledgeRecordingScopeFactory) -> None:
        self._catalogs = catalogs

    async def create_draft(
        self,
        recording_id: UUID,
        work_id: UUID,
        predicate: RecordingOriginPredicate,
        *,
        claim_id: UUID | None = None,
    ) -> RecordingOriginClaim:
        claim = RecordingOriginClaim.create_draft(
            recording_id,
            work_id,
            predicate,
            claim_id=claim_id,
        )
        async with self._catalogs() as (hk, music):
            await self._ensure_endpoints_exist(music, recording_id, work_id)
            await hk.recording_origin_claims.add(claim)
            await hk.commit()
            return claim

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
        async with self._catalogs() as (hk, _music):
            claim = await self._get(hk, claim_id, for_update=True)
            updated = claim.replace_content(
                explanation=explanation,
                temporal=temporal,
                geographic=geographic,
                provenance=provenance,
                evidence_status=evidence_status,
            )
            await hk.recording_origin_claims.save(updated)
            await hk.commit()
            return updated

    async def replace_evidence(
        self,
        claim_id: UUID,
        references: tuple[ClaimEvidenceReference, ...],
    ) -> RecordingOriginClaim:
        async with self._catalogs() as (hk, _music):
            claim = await self._get(hk, claim_id, for_update=True)
            for fragment_id in sorted({reference.source_fragment_id for reference in references}):
                if await hk.sources.get_fragment(fragment_id, for_update=True) is None:
                    raise SourceNotFound(str(fragment_id))
            updated = claim.replace_evidence(references)
            await hk.recording_origin_claims.save(updated)
            await hk.commit()
            return updated

    async def publish(self, claim_id: UUID) -> RecordingOriginClaim:
        async with self._catalogs() as (hk, music):
            claim = await self._get(hk, claim_id, for_update=True)
            await self._ensure_endpoints_published(music, claim.recording_id, claim.work_id)
            await self._ensure_evidence_fragments_reviewed(hk, claim)
            published = claim.publish()
            await hk.recording_origin_claims.save(published)
            await hk.commit()
            return published

    async def archive(self, claim_id: UUID) -> RecordingOriginClaim:
        async with self._catalogs() as (hk, _music):
            claim = await self._get(hk, claim_id, for_update=True)
            archived = claim.archive()
            await hk.recording_origin_claims.save(archived)
            await hk.commit()
            return archived

    @staticmethod
    async def _ensure_endpoints_exist(
        music: RecordingUnitOfWork,
        recording_id: UUID,
        work_id: UUID,
    ) -> None:
        if await music.recordings.get(recording_id) is None:
            raise EndpointRecordingMissing(str(recording_id))
        if await music.works.get(work_id) is None:
            raise EndpointWorkMissing(str(work_id))

    @staticmethod
    async def _ensure_endpoints_published(
        music: RecordingUnitOfWork,
        recording_id: UUID,
        work_id: UUID,
    ) -> None:
        if await music.recordings.get_published(recording_id, for_update=True) is None:
            raise EndpointRecordingNotPublished(str(recording_id))
        if await music.works.get_published(work_id, for_update=True) is None:
            raise EndpointWorkNotPublished(str(work_id))

    @staticmethod
    async def _ensure_evidence_fragments_reviewed(
        uow: HistoricalKnowledgeUnitOfWork,
        claim: RecordingOriginClaim,
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
    ) -> RecordingOriginClaim:
        claim = await uow.recording_origin_claims.get(claim_id, for_update=for_update)
        if claim is None:
            raise ClaimNotFound(str(claim_id))
        return claim
