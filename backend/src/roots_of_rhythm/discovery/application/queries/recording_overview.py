import logging
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import (
    GenreSummary,
    GroupSummary,
    PerformerSummary,
    SongSummary,
)
from roots_of_rhythm.discovery.application.dto.recordings import (
    ListeningGuideView,
    ListeningObservationView,
    RecordingCreditView,
    RecordingLyricsVersionView,
    RecordingOverviewResponse,
    RecordingWorkView,
)
from roots_of_rhythm.discovery.application.dto.songs import (
    SongPeriodView,
)
from roots_of_rhythm.discovery.application.errors.recordings import RecordingOverviewNotFound
from roots_of_rhythm.historical_knowledge.domain import origin_badge_values
from roots_of_rhythm.music_catalog.application.lyrics_body_projection import project_lyrics_version_body

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.public.recording_knowledge_reader import RecordingKnowledgeReader
    from roots_of_rhythm.music_catalog.public.recording_lyrics_reader import RecordingLyricsReader
    from roots_of_rhythm.music_catalog.public.recording_reader import RecordingReader
    from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReader

logger = logging.getLogger(__name__)


@runtime_checkable
class RecordingOverviewReader(Protocol):
    async def get(self, recording_id: UUID) -> RecordingOverviewResponse: ...


class RecordingOverviewQuery:
    def __init__(
        self,
        recordings: RecordingReader,
        people: PublishedPeopleReader,
        lyrics: RecordingLyricsReader,
        knowledge: RecordingKnowledgeReader,
    ) -> None:
        self._recordings = recordings
        self._people = people
        self._lyrics = lyrics
        self._knowledge = knowledge

    async def get(self, recording_id: UUID) -> RecordingOverviewResponse:
        data = await self._recordings.get_recording_overview(recording_id)
        recording = data.recording
        if recording is None:
            raise RecordingOverviewNotFound(str(recording_id))

        people_data = await self._people.get_published_by_ids(data.person_ids)
        persons = {person.id: person for person in people_data.persons}

        visible_credits = []
        for credit in recording.credits:
            summary: PerformerSummary | GroupSummary
            if credit.is_person_target:
                person = persons.get(credit.target_id)
                if person is None:
                    continue
                summary = PerformerSummary(str(person.id), person.canonical_name)
            elif credit.is_group_target:
                group = data.groups.get(credit.target_id)
                if group is None:
                    continue
                summary = GroupSummary(str(group.id), group.canonical_name)
            else:
                logger.warning(
                    "Not valid target kind '%s' about credit %s",
                    credit.target_kind,
                    credit.id,
                )
                continue

            visible_credits.append(
                RecordingCreditView(
                    credit.target_kind,
                    summary,
                    credit.billing_role,
                    credit.contribution_kind,
                    credit.instrument,
                    credit.credited_as,
                )
            )
        if not any(item.is_primary_billing for item in visible_credits):
            raise RecordingOverviewNotFound(str(recording_id))

        lyrics = await self._lyrics.get(recording)
        versions = [item.version for item in lyrics.items] + [
            translation for item in lyrics.items for translation in item.reading_translations
        ]
        knowledge = await self._knowledge.get_recording_data(
            recording_id,
            tuple(version.source_version_id for version in versions),
        )
        source_access_by_version = dict(knowledge.source_access_by_version)
        lyrics_views = []
        for item in lyrics.items:
            for version in (item.version, *item.reading_translations):
                disclosure = project_lyrics_version_body(
                    version,
                    source_access_by_version.get(version.source_version_id),
                )
                lyrics_views.append(
                    RecordingLyricsVersionView(
                        str(version.id),
                        version.language_tag,
                        version.label,
                        version.creation_method,
                        disclosure.body,
                        disclosure.body_unavailable_reason,
                        item.position,
                        item.confirmed_for_recording,
                    )
                )

        published_work_ids = set(data.works.keys())
        visible_claims = tuple(claim for claim in knowledge.origin_claims if claim.work_id in published_work_ids)
        origin_badges = origin_badge_values(visible_claims)

        work_views = [
            RecordingWorkView(SongSummary(str(work.id), work.canonical_title), usage.usage_kind, usage.position)
            for usage in recording.work_usages
            if (work := data.works.get(usage.work_id)) is not None
        ]
        if not work_views:
            raise RecordingOverviewNotFound(str(recording_id))

        return RecordingOverviewResponse(
            id=str(recording.id),
            title=recording.title,
            period=SongPeriodView.from_period(recording.recorded_period),
            description=recording.description,
            isrc=recording.isrc,
            first_release_date=None,
            works=work_views,
            credits=visible_credits,
            genres=sorted(
                (GenreSummary(str(item.id), item.content.canonical_name) for item in data.genres.values()),
                key=lambda item: item.name,
            ),
            lyrics=lyrics_views,
            listening_guide=None
            if knowledge.listening_guide is None
            else ListeningGuideView(
                [
                    ListeningObservationView(
                        item.feature,
                        item.explanation,
                        item.context,
                        item.position,
                        item.start_seconds,
                        item.end_seconds,
                    )
                    for item in knowledge.listening_guide.observations
                ]
            ),
            origin_badges=origin_badges,
        )
