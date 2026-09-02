from collections.abc import Callable
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
from roots_of_rhythm.discovery.application.recording_lyrics import RecordingLyricsProjectionQuery
from roots_of_rhythm.historical_knowledge.domain import origin_badge_values

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.application.ports import HistoricalKnowledgeUnitOfWork
    from roots_of_rhythm.music_catalog.application.lyrics_version_projection_service import (
        LyricsVersionProjectionService,
    )
    from roots_of_rhythm.music_catalog.application.ports import RecordingUnitOfWork
    from roots_of_rhythm.people_catalog.application.ports import PeopleCatalogUnitOfWork

type MusicFactory = Callable[[], RecordingUnitOfWork]
type PeopleFactory = Callable[[], PeopleCatalogUnitOfWork]
type KnowledgeFactory = Callable[[], HistoricalKnowledgeUnitOfWork]


@runtime_checkable
class RecordingOverviewReader(Protocol):
    async def get(self, recording_id: UUID) -> RecordingOverviewResponse: ...


class RecordingOverviewQuery:
    def __init__(
        self,
        music: MusicFactory,
        people: PeopleFactory,
        knowledge: KnowledgeFactory,
        lyrics_projection: LyricsVersionProjectionService,
    ) -> None:
        self._music = music
        self._people = people
        self._knowledge = knowledge
        self._recording_lyrics = RecordingLyricsProjectionQuery(music)
        self._lyrics_projection = lyrics_projection

    async def get(self, recording_id: UUID) -> RecordingOverviewResponse:
        async with self._music() as uow:
            recording = await uow.recordings.get_published(recording_id)
            if recording is None:
                raise RecordingOverviewNotFound(str(recording_id))
            works = await uow.works.get_published_by_ids([item.work_id for item in recording.work_usages])
            assignments = await uow.assignments.list_published_for_recording(recording_id)
            genres = await uow.genres.get_published_by_ids([item.concept_id for item in assignments])
            group_ids = sorted(item.target_id for item in recording.credits if item.is_group_target)
            groups = await uow.groups.get_published_by_ids(group_ids)

        person_ids = {item.target_id for item in recording.credits if item.is_person_target}
        async with self._people() as people:
            persons = await people.persons.get_published_by_ids(person_ids)
        visible_credits = []
        for credit in recording.credits:
            target = persons.get(credit.target_id) if credit.is_person_target else groups.get(credit.target_id)
            if target is None:
                continue
            summary = (
                PerformerSummary(str(target.id), target.canonical_name)
                if credit.is_person_target
                else GroupSummary(str(target.id), target.canonical_name)
            )
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

        lyrics = await self._recording_lyrics.get(recording)
        versions = [item.version for item in lyrics.items] + [
            translation for item in lyrics.items for translation in item.reading_translations
        ]
        disclosures = await self._lyrics_projection.disclose_bodies_for_versions(versions)
        disclosure_by_id = {version.id: disclosure for version, disclosure in zip(versions, disclosures, strict=True)}
        lyrics_views = []
        for item in lyrics.items:
            for version in (item.version, *item.reading_translations):
                disclosure = disclosure_by_id[version.id]
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

        async with self._knowledge() as hk:
            guide = await hk.listening_guides.get_published_for_recording(recording_id)
            claims_by_recording = await hk.recording_origin_claims.list_supported_published_for_recordings(
                [recording_id],
            )
        published_work_ids = set(works.keys())
        visible_claims = [
            claim for claim in claims_by_recording.get(recording_id, ()) if claim.work_id in published_work_ids
        ]
        origin_badges = origin_badge_values(visible_claims)

        work_views = [
            RecordingWorkView(SongSummary(str(work.id), work.canonical_title), usage.usage_kind, usage.position)
            for usage in recording.work_usages
            if (work := works.get(usage.work_id)) is not None
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
                (GenreSummary(str(item.id), item.content.canonical_name) for item in genres.values()),
                key=lambda item: item.name,
            ),
            lyrics=lyrics_views,
            listening_guide=None
            if guide is None
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
                    for item in guide.observations
                ]
            ),
            origin_badges=origin_badges,
        )
