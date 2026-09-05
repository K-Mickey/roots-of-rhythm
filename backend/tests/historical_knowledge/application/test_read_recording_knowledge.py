from uuid import uuid7

import pytest
from tests.historical_knowledge.fakes import (
    FakeSourceRepository,
    StubListeningGuideRepository,
    StubRecordingOriginClaimRepository,
)
from tests.support.scopes import fake_transaction_scope

from roots_of_rhythm.historical_knowledge.application.read_services.recording_knowledge import (
    RecordingKnowledgeReadService,
)
from roots_of_rhythm.historical_knowledge.domain import (
    EditorialStatus,
    EvidenceStatus,
    ListeningGuide,
    RecordingOriginClaim,
    RecordingOriginPredicate,
    Source,
    SourceAccessPolicy,
    SourceVersion,
)


@pytest.mark.asyncio
async def test_recording_knowledge_read_service_returns_guide_claims_and_source_access() -> None:
    recording_id = uuid7()
    work_id = uuid7()
    guide = ListeningGuide(
        id=uuid7(),
        recording_id=recording_id,
        observations=(),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    claim = RecordingOriginClaim(
        id=uuid7(),
        recording_id=recording_id,
        work_id=work_id,
        predicate=RecordingOriginPredicate.FIRST_RECORDING_OF,
        editorial_status=EditorialStatus.PUBLISHED,
        evidence_status=EvidenceStatus.SUPPORTED,
    )
    source = Source.create(
        "Lyrics",
        access_policy=SourceAccessPolicy.ALLOW_PUBLIC_BODY,
        source_id=uuid7(),
    )
    version = SourceVersion.create(source.id, "v1", version_id=uuid7())
    sources = FakeSourceRepository()
    sources.sources[source.id] = source
    sources.versions[version.id] = version
    guides = StubListeningGuideRepository({guide.id: guide})
    claims = StubRecordingOriginClaimRepository({recording_id: [claim]})
    service = RecordingKnowledgeReadService(
        fake_transaction_scope(),
        lambda _t: guides,
        lambda _t: claims,
        lambda _t: sources,
    )

    result = await service.get_recording_data(recording_id, [version.id])

    assert result.listening_guide is guide
    assert result.origin_claims == (claim,)
    assert result.source_access_by_version == ((version.id, SourceAccessPolicy.ALLOW_PUBLIC_BODY),)


@pytest.mark.asyncio
async def test_recording_knowledge_read_service_only_supported_published_claims() -> None:
    recording_id = uuid7()
    supported = RecordingOriginClaim(
        id=uuid7(),
        recording_id=recording_id,
        work_id=uuid7(),
        predicate=RecordingOriginPredicate.FIRST_RECORDING_OF,
        editorial_status=EditorialStatus.PUBLISHED,
        evidence_status=EvidenceStatus.SUPPORTED,
    )
    unverified = RecordingOriginClaim(
        id=uuid7(),
        recording_id=recording_id,
        work_id=uuid7(),
        predicate=RecordingOriginPredicate.FIRST_RELEASED_RECORDING_OF,
        editorial_status=EditorialStatus.PUBLISHED,
        evidence_status=EvidenceStatus.UNVERIFIED,
    )
    claims = StubRecordingOriginClaimRepository({recording_id: [supported, unverified]})
    service = RecordingKnowledgeReadService(
        fake_transaction_scope(),
        lambda _t: StubListeningGuideRepository(),
        lambda _t: claims,
        lambda _t: FakeSourceRepository(),
    )

    result = await service.get_recording_data(recording_id, [])

    assert result.origin_claims == (supported,)


@pytest.mark.asyncio
async def test_recording_knowledge_read_service_empty_when_no_guide_claims_or_versions() -> None:
    sources = FakeSourceRepository()
    service = RecordingKnowledgeReadService(
        fake_transaction_scope(),
        lambda _t: StubListeningGuideRepository(),
        lambda _t: StubRecordingOriginClaimRepository(),
        lambda _t: sources,
    )

    result = await service.get_recording_data(uuid7(), [])

    assert result.listening_guide is None
    assert result.origin_claims == ()
    assert result.source_access_by_version == ()
