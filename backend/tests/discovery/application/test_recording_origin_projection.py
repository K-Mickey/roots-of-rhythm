from uuid import UUID, uuid7

import pytest

from roots_of_rhythm.discovery.application.recording_overview import RecordingOverviewQuery
from roots_of_rhythm.discovery.application.song_overview import SongOverviewQuery
from roots_of_rhythm.historical_knowledge.domain import (
    EditorialStatus,
    EvidenceStatus,
    RecordingOriginClaim,
    RecordingOriginPredicate,
)
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    Group,
    GroupContent,
    MusicalWork,
    Recording,
    RecordingContent,
    RecordingCredit,
    RecordingCreditTargetKind,
    RecordingWorkUsage,
    RecordingWorkUsageKind,
    WorkContent,
)
from roots_of_rhythm.music_catalog.domain import (
    EditorialStatus as MusicEditorialStatus,
)
from tests.discovery.application.test_recording_overview import StubLyricsProjection
from tests.discovery.application.test_song_overview import StubLyricsProjection as SongStubLyricsProjection
from tests.discovery.application.test_song_overview_recordings import (
    _assignment,
    _genre,
    _recording,
)
from tests.historical_knowledge.fakes import StubHistoricalKnowledgeUnitOfWork
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork
from tests.people_catalog.fakes import FakePeopleCatalogUnitOfWork


def _published_origin_claim(
    recording_id: UUID,
    work_id: UUID,
    predicate: RecordingOriginPredicate,
    *,
    evidence_status: EvidenceStatus = EvidenceStatus.SUPPORTED,
    editorial_status: EditorialStatus = EditorialStatus.PUBLISHED,
) -> RecordingOriginClaim:
    return RecordingOriginClaim(
        id=uuid7(),
        recording_id=recording_id,
        work_id=work_id,
        predicate=predicate,
        editorial_status=editorial_status,
        evidence_status=evidence_status,
    )


@pytest.mark.asyncio
async def test_recording_overview_shows_supported_origin_badges_for_published_work() -> None:
    work_id = uuid7()
    group_id = uuid7()
    recording_id = uuid7()
    work = MusicalWork.create(
        work_id,
        WorkContent.create("Sixteen Tons"),
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    group = Group.create(
        group_id,
        GroupContent.create("Merle Travis"),
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    recording = Recording.create(
        recording_id,
        RecordingContent.create(
            "Sixteen Tons",
            recording_credits=(
                RecordingCredit.create(
                    uuid7(),
                    RecordingCreditTargetKind.GROUP,
                    group_id,
                    BillingRole.PRIMARY,
                ),
            ),
            work_usages=(RecordingWorkUsage.create(uuid7(), work_id, RecordingWorkUsageKind.COMPLETE),),
        ),
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    claims = {
        recording_id: [
            _published_origin_claim(recording_id, work_id, RecordingOriginPredicate.FIRST_RECORDING_OF),
            _published_origin_claim(
                recording_id,
                work_id,
                RecordingOriginPredicate.FIRST_RELEASED_RECORDING_OF,
                evidence_status=EvidenceStatus.UNVERIFIED,
            ),
        ]
    }
    query = RecordingOverviewQuery(
        lambda: FakeMusicCatalogUnitOfWork(
            {},
            groups={group_id: group},
            works={work_id: work},
            recordings={recording_id: recording},
        ),
        lambda: FakePeopleCatalogUnitOfWork({}),
        lambda: StubHistoricalKnowledgeUnitOfWork(claims),
        StubLyricsProjection(),  # type: ignore[arg-type]
    )

    response = await query.get(recording_id)

    assert response.origin_badges == ["first_recording_of"]


@pytest.mark.asyncio
async def test_song_overview_shows_origin_badges_only_for_current_work() -> None:
    work_id = uuid7()
    other_work_id = uuid7()
    jazz = _genre("Jazz")
    group = Group.create(
        uuid7(),
        GroupContent.create("Merle Travis"),
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    work = MusicalWork.create(
        work_id,
        WorkContent.create("Sixteen Tons"),
        editorial_status=MusicEditorialStatus.PUBLISHED,
    )
    recording = _recording(
        work_id,
        title="Sixteen Tons",
        group=group,
        usage_kind=RecordingWorkUsageKind.COMPLETE,
    )
    assignment = _assignment(recording.id, jazz)
    claims = {
        recording.id: [
            _published_origin_claim(recording.id, work_id, RecordingOriginPredicate.FIRST_RECORDING_OF),
            _published_origin_claim(recording.id, other_work_id, RecordingOriginPredicate.RECORDED_BY_WORK_AUTHOR),
        ]
    }
    query = SongOverviewQuery(
        lambda: FakeMusicCatalogUnitOfWork(
            {jazz.id: jazz},
            {assignment.id: assignment},
            groups={group.id: group},
            works={work_id: work},
            recordings={recording.id: recording},
        ),
        lambda: FakePeopleCatalogUnitOfWork({}),
        lambda: StubHistoricalKnowledgeUnitOfWork(claims),
        SongStubLyricsProjection(),  # type: ignore[arg-type]
    )

    response = await query.get(work_id)

    assert response.recordings[0].origin_badges == ["first_recording_of"]
