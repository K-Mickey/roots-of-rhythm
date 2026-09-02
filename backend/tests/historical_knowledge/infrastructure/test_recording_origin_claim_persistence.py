from typing import TYPE_CHECKING
from uuid import uuid7

import pytest

from roots_of_rhythm.historical_knowledge.application import (
    CreateRecordingOriginClaim,
    PublishRecordingOriginClaim,
    RecordingOriginClaimService,
    SourceService,
    UniqueConstraintViolation,
)
from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EvidenceRole,
    EvidenceStatus,
    GeographicContext,
    HistoricalPeriod,
    RecordingOriginPredicate,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.historical_knowledge.infrastructure.recording_origin_claim_repository import (
    SqlAlchemyRecordingOriginClaimRepository,
)
from roots_of_rhythm.historical_knowledge.infrastructure.source_repository import SqlAlchemySourceRepository
from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import SqlAlchemyHistoricalKnowledgeUnitOfWork
from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.infrastructure.transaction import SqlAlchemyTransactionScope, sqlalchemy_session
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    MusicalWork,
    Recording,
    RecordingContent,
    RecordingCredit,
    RecordingCreditTargetKind,
    RecordingWorkUsage,
    RecordingWorkUsageKind,
    WorkContent,
)
from roots_of_rhythm.music_catalog.domain import EditorialStatus as MusicEditorialStatus
from roots_of_rhythm.music_catalog.infrastructure.musical_work_repository import SqlAlchemyMusicalWorkRepository
from roots_of_rhythm.music_catalog.infrastructure.recording_repository import SqlAlchemyRecordingRepository
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

    from roots_of_rhythm.application.transaction import Transaction

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_recording_origin_claim_lifecycle_and_unique_constraint(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    recording_id, work_id = uuid7(), uuid7()
    work = MusicalWork.create(
        work_id,
        WorkContent.create("Work", provenance="Editorial source"),
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    recording = Recording.create(
        recording_id,
        RecordingContent.create(
            "Take",
            recording_credits=(
                RecordingCredit.create(
                    uuid7(),
                    RecordingCreditTargetKind.PERSON,
                    uuid7(),
                    BillingRole.PRIMARY,
                ),
            ),
            work_usages=(RecordingWorkUsage.create(uuid7(), work_id, RecordingWorkUsageKind.COMPLETE),),
        ),
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as music_uow:
        await music_uow.works.add(work)
        await music_uow.recordings.add(recording)
        await music_uow.commit()

    def hk_uow() -> SqlAlchemyHistoricalKnowledgeUnitOfWork:
        return SqlAlchemyHistoricalKnowledgeUnitOfWork(session_factory)

    source_service = SourceService(hk_uow)
    source = await source_service.create_source("Institutional source")
    version = await source_service.create_version(source.id, "v1")
    fragment = await source_service.create_fragment(version.id)
    await source_service.mark_fragment_reviewed(fragment.id)

    transaction_scope = SqlAlchemyTransactionScope(session_factory)

    def claim_repository(transaction: Transaction) -> SqlAlchemyRecordingOriginClaimRepository:
        return SqlAlchemyRecordingOriginClaimRepository(sqlalchemy_session(transaction))

    def source_repository(transaction: Transaction) -> SqlAlchemySourceRepository:
        return SqlAlchemySourceRepository(sqlalchemy_session(transaction))

    def recording_repository(transaction: Transaction) -> SqlAlchemyRecordingRepository:
        return SqlAlchemyRecordingRepository(sqlalchemy_session(transaction))

    def work_repository(transaction: Transaction) -> SqlAlchemyMusicalWorkRepository:
        return SqlAlchemyMusicalWorkRepository(sqlalchemy_session(transaction))

    service = RecordingOriginClaimService(transaction_scope, claim_repository, source_repository)
    create = CreateRecordingOriginClaim(
        transaction_scope,
        claim_repository,
        recording_repository,
        work_repository,
    )
    publish = PublishRecordingOriginClaim(
        transaction_scope,
        claim_repository,
        recording_repository,
        work_repository,
        source_repository,
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
    await service.replace_evidence(
        claim.id,
        (ClaimEvidenceReference.create(fragment.id, EvidenceRole.SUPPORTS),),
    )
    published = await publish.execute(claim.id)

    assert published.is_published
    async with hk_uow() as historical_uow:
        assert await historical_uow.recording_origin_claims.get(claim.id) == published

    with pytest.raises(UniqueConstraintViolation):
        await create.execute(recording_id, work_id, RecordingOriginPredicate.FIRST_RECORDING_OF)

    async with hk_uow() as historical_uow:
        assert await historical_uow.recording_origin_claims.get(claim.id) == published
