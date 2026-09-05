from typing import TYPE_CHECKING
from uuid import UUID, uuid7

import pytest
from tests.music_catalog.fakes import (
    FakeClassificationAssignmentRepository,
    FakeGenreRepository,
    FakeGroupRepository,
    FakeLyricsVersionCreditRepository,
    FakeLyricsVersionRelationRepository,
    FakeLyricsVersionRepository,
    FakeMusicalWorkRepository,
    FakeRecordingRepository,
    FakeWorkCreditRepository,
    FakeWorkRelationRepository,
)
from tests.support.scopes import fake_transaction_scope

from roots_of_rhythm.music_catalog.application.read_services.song_overview import SongOverviewReadService
from roots_of_rhythm.music_catalog.domain import (
    ClassificationAssignment,
    ClassificationContent,
    ClassificationTargetKind,
    EditorialStatus,
    Genre,
    MusicalWork,
    Recording,
    RecordingContent,
    RecordingWorkUsage,
    RecordingWorkUsageKind,
    WorkContent,
)

if TYPE_CHECKING:
    from collections.abc import Collection


class SpyGenreRepository(FakeGenreRepository):
    def __init__(self, genres: dict[UUID, Genre]) -> None:
        super().__init__(genres)
        self.calls: list[set[UUID]] = []

    async def get_published_by_ids(
        self,
        genre_ids: "Collection[UUID]",
        *,
        for_update: bool = False,
    ) -> dict[UUID, Genre]:
        self.calls.append(set(genre_ids))
        return await super().get_published_by_ids(genre_ids, for_update=for_update)


@pytest.mark.asyncio
async def test_song_overview_read_service_batches_work_and_recording_genres_once() -> None:
    work_id = uuid7()
    recording_id = uuid7()
    work_genre = _genre("Work genre")
    recording_genre = _genre("Recording genre")
    work = MusicalWork.create(
        work_id,
        WorkContent.create("Song", provenance="Editorial note."),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    recording = Recording.create(
        recording_id,
        RecordingContent.create(
            "Recording",
            work_usages=(RecordingWorkUsage.create(uuid7(), work_id, RecordingWorkUsageKind.COMPLETE),),
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    assignments = {
        assignment.id: assignment
        for assignment in (
            _assignment(ClassificationTargetKind.MUSICAL_WORK, work_id, work_genre.id),
            _assignment(ClassificationTargetKind.RECORDING, recording_id, recording_genre.id),
        )
    }
    genres = SpyGenreRepository({work_genre.id: work_genre, recording_genre.id: recording_genre})
    scope = fake_transaction_scope()
    service = SongOverviewReadService(
        scope,
        lambda _t: FakeMusicalWorkRepository({work_id: work}),
        lambda _t: FakeWorkCreditRepository({}),
        lambda _t: FakeClassificationAssignmentRepository(assignments),
        lambda _t: FakeWorkRelationRepository({}),
        lambda _t: FakeLyricsVersionRepository({}),
        lambda _t: FakeLyricsVersionCreditRepository({}),
        lambda _t: FakeLyricsVersionRelationRepository({}),
        lambda _t: FakeRecordingRepository({recording_id: recording}),
        lambda _t: genres,
        lambda _t: FakeGroupRepository({}),
    )

    data = await service.get_song_data(work_id)

    assert genres.calls == [{work_genre.id, recording_genre.id}]
    assert data.genres == (work_genre,)
    assert data.recording_genres == (recording_genre,)


def _genre(name: str) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Definition."),
        editorial_status=EditorialStatus.PUBLISHED,
    )


def _assignment(target_kind: ClassificationTargetKind, target_id: UUID, genre_id: UUID) -> ClassificationAssignment:
    return ClassificationAssignment(
        id=uuid7(),
        target_kind=target_kind,
        target_id=target_id,
        concept_id=genre_id,
        explanation="Classification explanation.",
        provenance="Editorial review.",
        editorial_status=EditorialStatus.PUBLISHED,
    )
