from datetime import UTC, datetime
from uuid import UUID, uuid7

import pytest
from tests.historical_knowledge.fakes import (
    FakeHistoricalKnowledgeUnitOfWork,
    FakeSourceRepository,
    StubListeningGuideRepository,
)
from tests.music_catalog.fakes import FakeRecordingRepository

from roots_of_rhythm.historical_knowledge.application import (
    ListeningGuideNotFound,
    ListeningGuideRecordingNotPublished,
    ListeningGuideService,
    PublishListeningGuide,
    ReplaceListeningGuideObservations,
)
from roots_of_rhythm.historical_knowledge.domain import EditorialStatus, ListeningObservation
from roots_of_rhythm.music_catalog.domain import EditorialStatus as MusicEditorialStatus
from roots_of_rhythm.music_catalog.domain import Recording


def _operations(
    recordings: dict[UUID, Recording],
) -> tuple[
    ListeningGuideService,
    ReplaceListeningGuideObservations,
    PublishListeningGuide,
    StubListeningGuideRepository,
    FakeRecordingRepository,
    FakeHistoricalKnowledgeUnitOfWork,
]:
    guide_repository = StubListeningGuideRepository()
    recording_repository = FakeRecordingRepository(recordings)
    transaction = FakeHistoricalKnowledgeUnitOfWork({}, FakeSourceRepository())
    transaction.listening_guides = guide_repository
    return (
        ListeningGuideService(
            lambda: transaction,
            lambda _transaction: guide_repository,
        ),
        ReplaceListeningGuideObservations(
            lambda: transaction,
            lambda _transaction: guide_repository,
            lambda _transaction: recording_repository,
        ),
        PublishListeningGuide(
            lambda: transaction,
            lambda _transaction: guide_repository,
            lambda _transaction: recording_repository,
        ),
        guide_repository,
        recording_repository,
        transaction,
    )


def _observation(feature: str = "Theme") -> ListeningObservation:
    return ListeningObservation.create(feature, "Notice it.", uuid7(), datetime.now(UTC))


@pytest.mark.asyncio
async def test_listening_guide_lifecycle_rechecks_only_published_recording() -> None:
    recording_id = uuid7()
    service, replace, publish, guides, recordings, transaction = _operations(
        {
            recording_id: Recording(
                recording_id,
                "Take",
                editorial_status=MusicEditorialStatus.PUBLISHED,
            )
        }
    )

    guide = await service.create_draft(recording_id, (_observation(),))
    guide = await replace.execute(guide.id, (_observation("Solo"),))
    assert recordings.locked_ids == []

    guide = await publish.execute(guide.id)
    assert guide.editorial_status is EditorialStatus.PUBLISHED
    assert recordings.locked_ids == [recording_id]

    guide = await replace.execute(guide.id, (_observation("Ending"),))
    archived = await service.archive(guide.id)

    assert archived.editorial_status is EditorialStatus.ARCHIVED
    assert recordings.locked_ids == [recording_id, recording_id]
    assert guides.locked_ids == [guide.id] * 4
    assert transaction.commits == 5


@pytest.mark.asyncio
async def test_publish_reports_missing_guide_and_unpublished_recording() -> None:
    recording_id = uuid7()
    service, _replace, publish, _guides, _recordings, _transaction = _operations(
        {recording_id: Recording(recording_id, "Take")}
    )

    with pytest.raises(ListeningGuideNotFound):
        await publish.execute(uuid7())

    guide = await service.create_draft(recording_id, (_observation(),))
    with pytest.raises(ListeningGuideRecordingNotPublished, match=str(recording_id)):
        await publish.execute(guide.id)


@pytest.mark.asyncio
async def test_replace_published_guide_requires_published_recording() -> None:
    recording_id = uuid7()
    recording_data = {
        recording_id: Recording(
            recording_id,
            "Take",
            editorial_status=MusicEditorialStatus.PUBLISHED,
        )
    }
    service, replace, publish, _guides, _recordings, _transaction = _operations(recording_data)
    guide = await service.create_draft(recording_id, (_observation(),))
    await publish.execute(guide.id)
    recording_data[recording_id] = Recording(recording_id, "Take")

    with pytest.raises(ListeningGuideRecordingNotPublished, match=str(recording_id)):
        await replace.execute(guide.id, (_observation("Solo"),))
