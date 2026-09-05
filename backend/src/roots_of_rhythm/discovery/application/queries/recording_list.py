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
from roots_of_rhythm.discovery.application.projections.recording_credits import project_primary_credits

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.public.recording_reader import RecordingReader
    from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReader


@runtime_checkable
class RecordingListReader(Protocol):
    async def list(self) -> RecordingListResponse: ...


class RecordingListQuery:
    def __init__(self, recordings: RecordingReader, people: PublishedPeopleReader) -> None:
        self._recordings = recordings
        self._people = people

    async def list(self) -> RecordingListResponse:
        data = await self._recordings.list_overview()
        recordings = data.recordings
        if not recordings:
            return RecordingListResponse(items=[])
        assignments_by_recording = data.assignments_by_recording
        genres = data.genres
        groups = data.groups

        people_data = await self._people.get_published_by_ids(data.person_ids)
        persons = {person.id: person for person in people_data.persons}

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
