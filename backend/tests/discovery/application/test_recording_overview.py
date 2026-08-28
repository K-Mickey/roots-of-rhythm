from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.errors import RecordingOverviewNotFound
from roots_of_rhythm.discovery.application.recording_overview import RecordingOverviewQuery
from roots_of_rhythm.music_catalog.application.lyrics_body_projection import LyricsBodyDisclosure
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    EditorialStatus,
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
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork
from tests.people_catalog.fakes import FakePeopleCatalogUnitOfWork


class StubLyricsProjection:
    async def disclose_bodies_for_versions(self, versions: tuple[object, ...]) -> list[LyricsBodyDisclosure]:
        return [LyricsBodyDisclosure(body=None, body_unavailable_reason=None) for _ in versions]


class StubListeningGuideRepository:
    async def get_published_for_recording(self, _recording_id: object) -> None:
        return None


class StubHistoricalKnowledgeUnitOfWork:
    def __init__(self) -> None:
        self.listening_guides = StubListeningGuideRepository()

    async def __aenter__(self) -> "StubHistoricalKnowledgeUnitOfWork":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


@pytest.mark.asyncio
async def test_recording_overview_raises_when_no_published_works_remain() -> None:
    work_id = uuid7()
    group_id = uuid7()
    recording_id = uuid7()
    draft_work = MusicalWork.create(
        work_id,
        WorkContent.create("Hidden Work"),
        editorial_status=EditorialStatus.DRAFT,
    )
    group = Group.create(
        group_id,
        GroupContent.create("Dave Brubeck Quartet"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    recording = Recording.create(
        recording_id,
        RecordingContent.create(
            "Take Five",
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
        editorial_status=EditorialStatus.PUBLISHED,
    )
    query = RecordingOverviewQuery(
        lambda: FakeMusicCatalogUnitOfWork(
            {},
            groups={group_id: group},
            works={work_id: draft_work},
            recordings={recording_id: recording},
        ),
        lambda: FakePeopleCatalogUnitOfWork({}),
        lambda: StubHistoricalKnowledgeUnitOfWork(),
        StubLyricsProjection(),  # type: ignore[arg-type]
    )

    with pytest.raises(RecordingOverviewNotFound):
        await query.get(recording_id)
