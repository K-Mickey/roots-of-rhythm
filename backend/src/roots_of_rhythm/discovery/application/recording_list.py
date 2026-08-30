from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import (
    GenreSummary,
)
from roots_of_rhythm.discovery.application.dto.recordings import (
    RecordingListItem,
    RecordingListResponse,
)
from roots_of_rhythm.discovery.application.dto.songs import (
    SongPeriodView,
)
from roots_of_rhythm.discovery.application.recording_credits import project_primary_credits
from roots_of_rhythm.music_catalog.domain import BillingRole, RecordingCreditTargetKind

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.application.ports import RecordingUnitOfWork
    from roots_of_rhythm.people_catalog.application.ports import PeopleCatalogUnitOfWork

type MusicFactory = Callable[[], RecordingUnitOfWork]
type PeopleFactory = Callable[[], PeopleCatalogUnitOfWork]


@runtime_checkable
class RecordingListReader(Protocol):
    async def list(self) -> RecordingListResponse: ...


class RecordingListQuery:
    def __init__(self, music: MusicFactory, people: PeopleFactory) -> None:
        self._music = music
        self._people = people

    async def list(self) -> RecordingListResponse:
        async with self._music() as uow:
            recordings = await uow.recordings.list_published()
            if not recordings:
                return RecordingListResponse(items=[])
            recording_ids = [recording.id for recording in recordings]
            assignments_by_recording = await uow.assignments.list_published_for_recordings(recording_ids)
            genre_ids = {
                assignment.concept_id for assignments in assignments_by_recording.values() for assignment in assignments
            }
            genres = await uow.genres.get_published_by_ids(genre_ids)

        person_ids = {
            credit.target_id
            for recording in recordings
            for credit in recording.credits
            if credit.billing_role is BillingRole.PRIMARY and credit.target_kind is RecordingCreditTargetKind.PERSON
        }
        async with self._people() as people_uow:
            persons = await people_uow.persons.get_published_by_ids(person_ids)
        group_ids = sorted(
            {
                credit.target_id
                for recording in recordings
                for credit in recording.credits
                if credit.billing_role is BillingRole.PRIMARY and credit.target_kind is RecordingCreditTargetKind.GROUP
            }
        )
        async with self._music() as uow:
            groups = await uow.groups.get_published_by_ids(group_ids)

        items: list[RecordingListItem] = []
        for recording in recordings:
            primary_credits = project_primary_credits(recording, persons, groups)
            if not primary_credits:
                continue
            recording_genres = []
            for assignment in assignments_by_recording.get(recording.id, ()):
                genre = genres.get(assignment.concept_id)
                if genre is not None:
                    recording_genres.append(GenreSummary(str(genre.id), genre.content.canonical_name))
            recording_genres = sorted(
                recording_genres,
                key=lambda item: item.name,
            )
            items.append(
                RecordingListItem(
                    id=str(recording.id),
                    title=recording.title,
                    period=SongPeriodView.from_period(recording.recorded_period),
                    primary_credits=primary_credits,
                    genres=recording_genres,
                )
            )

        items.sort(
            key=lambda item: (
                item.title.casefold(),
                tuple(sorted(credit.target.name.casefold() for credit in item.primary_credits)),
                item.id,
            )
        )
        return RecordingListResponse(items=items)
