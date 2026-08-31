from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid7

import pytest
from tests.historical_knowledge.fakes import (
    FakeHistoricalKnowledgeUnitOfWork,
    FakeSourceRepository,
    StubRecordingOriginClaimRepository,
)
from tests.music_catalog.fakes import FakeMusicalWorkRepository, FakeRecordingRepository

from roots_of_rhythm.historical_knowledge.application import (
    ClaimNotFound,
    CreateRecordingOriginClaim,
    EndpointRecordingMissing,
    EndpointRecordingNotPublished,
    EndpointWorkMissing,
    EndpointWorkNotPublished,
    EvidenceFragmentNotReviewed,
    PublishRecordingOriginClaim,
    RecordingOriginClaimService,
    SourceNotFound,
    UniqueConstraintViolation,
)
from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EditorialStatus,
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    GeographicContext,
    HistoricalPeriod,
    RecordingOriginClaim,
    RecordingOriginPredicate,
    SourceFragment,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.music_catalog.domain import EditorialStatus as MusicEditorialStatus
from roots_of_rhythm.music_catalog.domain import MusicalWork, Recording

if TYPE_CHECKING:
    from collections.abc import Collection


class TrackingSourceRepository(FakeSourceRepository):
    def __init__(self) -> None:
        super().__init__()
        self.locked_batches: list[set[UUID]] = []

    async def get_fragments_by_ids(
        self,
        fragment_ids: Collection[UUID],
        *,
        for_update: bool = False,
    ) -> dict[UUID, SourceFragment]:
        if for_update:
            self.locked_batches.append(set(fragment_ids))
        return await super().get_fragments_by_ids(fragment_ids, for_update=for_update)


def _operations(
    recordings: dict[UUID, Recording],
    works: dict[UUID, MusicalWork],
    *,
    claim_repository: StubRecordingOriginClaimRepository | None = None,
    sources: TrackingSourceRepository | None = None,
) -> tuple[
    RecordingOriginClaimService,
    CreateRecordingOriginClaim,
    PublishRecordingOriginClaim,
    StubRecordingOriginClaimRepository,
    TrackingSourceRepository,
    FakeHistoricalKnowledgeUnitOfWork,
]:
    origin_claims = claim_repository or StubRecordingOriginClaimRepository()
    source_repository = sources or TrackingSourceRepository()
    transaction = FakeHistoricalKnowledgeUnitOfWork({}, source_repository)
    transaction.recording_origin_claims = origin_claims
    recording_repository = FakeRecordingRepository(recordings)
    work_repository = FakeMusicalWorkRepository(works)

    return (
        RecordingOriginClaimService(
            lambda: transaction,
            lambda _transaction: origin_claims,
            lambda _transaction: source_repository,
        ),
        CreateRecordingOriginClaim(
            lambda: transaction,
            lambda _transaction: origin_claims,
            lambda _transaction: recording_repository,
            lambda _transaction: work_repository,
        ),
        PublishRecordingOriginClaim(
            lambda: transaction,
            lambda _transaction: origin_claims,
            lambda _transaction: recording_repository,
            lambda _transaction: work_repository,
            lambda _transaction: source_repository,
        ),
        origin_claims,
        source_repository,
        transaction,
    )


@pytest.mark.asyncio
async def test_recording_origin_claim_lifecycle_uses_locked_batch_evidence() -> None:
    recording_id, work_id, fragment_id = uuid7(), uuid7(), uuid7()
    service, create, publish, _claims, sources, transaction = _operations(
        {recording_id: Recording(recording_id, "Take", editorial_status=MusicEditorialStatus.PUBLISHED)},
        {
            work_id: MusicalWork(
                work_id,
                "Work",
                provenance="Editorial source",
                editorial_status=MusicEditorialStatus.PUBLISHED,
            )
        },
    )
    sources.fragments[fragment_id] = SourceFragment(
        fragment_id,
        uuid7(),
        FragmentReviewStatus.REVIEWED,
    )

    claim = await create.execute(recording_id, work_id, RecordingOriginPredicate.FIRST_RECORDING_OF)
    claim = await service.replace_content(
        claim.id,
        explanation="Earliest known recording.",
        temporal=HistoricalPeriod.create("1946", TemporalBound(1946, TemporalPrecision.EXACT_YEAR)),
        geographic=GeographicContext.create("United States"),
        provenance=ClaimProvenance.create("Editorial source"),
        evidence_status=EvidenceStatus.SUPPORTED,
    )
    claim = await service.replace_evidence(
        claim.id,
        (ClaimEvidenceReference.create(fragment_id, EvidenceRole.SUPPORTS),),
    )
    published = await publish.execute(claim.id)
    archived = await service.archive(claim.id)

    assert published.editorial_status is EditorialStatus.PUBLISHED
    assert archived.editorial_status is EditorialStatus.ARCHIVED
    assert sources.locked_batches == [{fragment_id}, {fragment_id}]
    assert transaction.commits == 5


@pytest.mark.asyncio
async def test_create_requires_recording_then_work() -> None:
    recording_id, work_id = uuid7(), uuid7()
    _service, create, _publish, _claims, _sources, _transaction = _operations({}, {})
    with pytest.raises(EndpointRecordingMissing, match=str(recording_id)):
        await create.execute(recording_id, work_id, RecordingOriginPredicate.FIRST_RECORDING_OF)

    _service, create, _publish, _claims, _sources, _transaction = _operations(
        {recording_id: Recording(recording_id, "Take")},
        {},
    )
    with pytest.raises(EndpointWorkMissing, match=str(work_id)):
        await create.execute(recording_id, work_id, RecordingOriginPredicate.FIRST_RECORDING_OF)


@pytest.mark.asyncio
async def test_publish_reports_missing_claim_unpublished_recording_and_invalid_evidence() -> None:
    recording_id, work_id, fragment_id = uuid7(), uuid7(), uuid7()
    recordings = {recording_id: Recording(recording_id, "Take")}
    works = {work_id: MusicalWork(work_id, "Work")}
    service, create, publish, _claims, sources, _transaction = _operations(recordings, works)
    with pytest.raises(ClaimNotFound):
        await publish.execute(uuid7())

    claim = await create.execute(recording_id, work_id, RecordingOriginPredicate.FIRST_RECORDING_OF)
    with pytest.raises(EndpointRecordingNotPublished):
        await publish.execute(claim.id)

    claim = await service.replace_content(
        claim.id,
        explanation="Earliest known recording.",
        temporal=HistoricalPeriod.create("1946", TemporalBound(1946, TemporalPrecision.EXACT_YEAR)),
        geographic=GeographicContext.create("United States"),
        provenance=ClaimProvenance.create("Editorial source"),
        evidence_status=EvidenceStatus.SUPPORTED,
    )
    with pytest.raises(SourceNotFound, match=str(fragment_id)):
        await service.replace_evidence(
            claim.id,
            (ClaimEvidenceReference.create(fragment_id, EvidenceRole.SUPPORTS),),
        )
    sources.fragments[fragment_id] = SourceFragment(fragment_id, uuid7())
    await service.replace_evidence(
        claim.id,
        (ClaimEvidenceReference.create(fragment_id, EvidenceRole.SUPPORTS),),
    )
    recordings[recording_id] = Recording(
        recording_id,
        "Take",
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    with pytest.raises(EndpointWorkNotPublished):
        await publish.execute(claim.id)

    works[work_id] = MusicalWork(
        work_id,
        "Work",
        provenance="Editorial source",
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    with pytest.raises(EvidenceFragmentNotReviewed, match=str(fragment_id)):
        await publish.execute(claim.id)


@pytest.mark.asyncio
async def test_create_preserves_repository_unique_conflict() -> None:
    class ConflictingRepository(StubRecordingOriginClaimRepository):
        async def add(self, claim: RecordingOriginClaim) -> None:
            del claim
            raise UniqueConstraintViolation("origin constraint")

    recording_id, work_id = uuid7(), uuid7()
    _service, create, _publish, _claims, _sources, _transaction = _operations(
        {recording_id: Recording(recording_id, "Take")},
        {work_id: MusicalWork(work_id, "Work")},
        claim_repository=ConflictingRepository(),
    )
    with pytest.raises(UniqueConstraintViolation):
        await create.execute(recording_id, work_id, RecordingOriginPredicate.FIRST_RECORDING_OF)
