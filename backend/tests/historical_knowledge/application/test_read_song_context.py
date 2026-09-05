from uuid import uuid7

import pytest
from tests.historical_knowledge.fakes import FakeSourceRepository, StubRecordingOriginClaimRepository
from tests.support.scopes import fake_transaction_scope

from roots_of_rhythm.historical_knowledge.application.read_services.song_context import SongContextReadService
from roots_of_rhythm.historical_knowledge.domain import (
    EditorialStatus,
    EvidenceStatus,
    RecordingOriginClaim,
    RecordingOriginPredicate,
    Source,
    SourceAccessPolicy,
    SourceVersion,
)


@pytest.mark.asyncio
async def test_song_context_read_service_returns_source_access_and_claims() -> None:
    source = Source.create(
        "Lyrics",
        access_policy=SourceAccessPolicy.ALLOW_PUBLIC_BODY,
        source_id=uuid7(),
    )
    version = SourceVersion.create(source.id, "v1", version_id=uuid7())
    sources = FakeSourceRepository()
    sources.sources[source.id] = source
    sources.versions[version.id] = version
    recording_id = uuid7()
    claim = RecordingOriginClaim(
        id=uuid7(),
        recording_id=recording_id,
        work_id=uuid7(),
        predicate=RecordingOriginPredicate.FIRST_RECORDING_OF,
        editorial_status=EditorialStatus.PUBLISHED,
        evidence_status=EvidenceStatus.SUPPORTED,
    )
    claims = StubRecordingOriginClaimRepository({recording_id: [claim]})
    service = SongContextReadService(
        fake_transaction_scope(),
        lambda _t: claims,
        lambda _t: sources,
    )

    result = await service.get_song_data([version.id], [recording_id])

    assert result.source_access_by_version == ((version.id, SourceAccessPolicy.ALLOW_PUBLIC_BODY),)
    assert result.origin_claims == (claim,)


@pytest.mark.asyncio
async def test_song_context_read_service_empty_when_no_ids() -> None:
    sources = FakeSourceRepository()
    service = SongContextReadService(
        fake_transaction_scope(),
        lambda _t: StubRecordingOriginClaimRepository(),
        lambda _t: sources,
    )

    result = await service.get_song_data([], [])

    assert result.source_access_by_version == ()
    assert result.origin_claims == ()
