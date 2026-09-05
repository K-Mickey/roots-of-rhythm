from asyncio import gather
from collections import defaultdict
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import (
    ExternalIdentityView,
    GenreSummary,
    PerformerSummary,
    SongSummary,
)
from roots_of_rhythm.discovery.application.dto.songs import (
    LyricsVersionRelationView,
    LyricsVersionSummary,
    RelatedWorkView,
    SongLyricsVersionView,
    SongOverviewResponse,
    SongPeriodView,
    SongRecordingGenreFacet,
    SongRecordingSummary,
    SongWorkCreditView,
)
from roots_of_rhythm.discovery.application.errors.songs import SongOverviewNotFound
from roots_of_rhythm.discovery.application.projections.recording_credits import project_primary_credits
from roots_of_rhythm.historical_knowledge.domain import origin_badge_values
from roots_of_rhythm.music_catalog.application.lyrics_body_projection import project_lyrics_version_body

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import RecordingOriginClaim
    from roots_of_rhythm.historical_knowledge.public.song_context_reader import SongHistoricalKnowledgeReader
    from roots_of_rhythm.music_catalog.domain import (
        ClassificationAssignment,
        Genre,
        Group,
        LyricsVersion,
        LyricsVersionCredit,
        LyricsVersionRelation,
        Recording,
        WorkCredit,
    )
    from roots_of_rhythm.music_catalog.public.song_overview_reader import SongMusicReader
    from roots_of_rhythm.people_catalog.domain import Person
    from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReader


@runtime_checkable
class SongOverviewReader(Protocol):
    async def get(self, song_id: UUID) -> SongOverviewResponse: ...


class SongOverviewQuery:
    def __init__(
        self,
        music: SongMusicReader,
        people: PublishedPeopleReader,
        knowledge: SongHistoricalKnowledgeReader,
    ) -> None:
        self._music = music
        self._people = people
        self._knowledge = knowledge

    async def get(self, song_id: UUID) -> SongOverviewResponse:
        music = await self._music.get_song_data(song_id)
        if music.work is None:
            raise SongOverviewNotFound(str(song_id))

        outbound_relations = [relation for relation in music.work_relations if relation.source_work_id == song_id]
        lyrics_credits_by_version = {
            version.id: [credit for credit in music.lyrics_credits if credit.lyrics_version_id == version.id]
            for version in music.lyrics_versions
        }
        lyrics_relations_by_version = {
            version.id: [
                relation
                for relation in music.lyrics_relations
                if version.id in {relation.source_lyrics_version_id, relation.target_lyrics_version_id}
            ]
            for version in music.lyrics_versions
        }
        related_works = {item.id: item for item in music.related_works}
        related_lyrics_versions = {item.id: item for item in (*music.lyrics_versions, *music.related_lyrics_versions)}
        recording_assignments = {
            recording.id: [item for item in music.recording_assignments if item.target_id == recording.id]
            for recording in music.recordings
        }

        person_ids = {credit.person_id for credit in music.work_credits}
        for version_credits in lyrics_credits_by_version.values():
            person_ids.update(credit.person_id for credit in version_credits)
        person_ids.update(
            credit.target_id
            for recording in music.recordings
            for credit in recording.credits
            if credit.is_primary_billing and credit.is_person_target
        )

        people, knowledge = await gather(
            self._people.get_published_by_ids(person_ids),
            self._knowledge.get_song_data(
                tuple(version.source_version_id for version in music.lyrics_versions),
                tuple(recording.id for recording in music.recordings),
            ),
        )
        persons = {person.id: person for person in people.persons}
        source_access_by_version = dict(knowledge.source_access_by_version)
        body_disclosures = [
            project_lyrics_version_body(version, source_access_by_version.get(version.source_version_id))
            for version in music.lyrics_versions
        ]
        loaded_claims = {
            recording.id: [claim for claim in knowledge.origin_claims if claim.recording_id == recording.id]
            for recording in music.recordings
        }
        origin_claims_by_recording = {
            recording_id: [claim for claim in claims if claim.work_id == song_id]
            for recording_id, claims in loaded_claims.items()
        }

        recording_genres_view, recordings_view = _project_song_recordings(
            song_id,
            list(music.recordings),
            recording_assignments,
            {item.id: item for item in music.recording_genres},
            persons,
            {item.id: item for item in music.groups},
            origin_claims_by_recording,
        )

        return SongOverviewResponse(
            id=str(music.work.id),
            name=music.work.canonical_title,
            aliases=list(music.work.aliases),
            description=music.work.description,
            period=SongPeriodView.from_period(music.work.period),
            external_identities=[
                ExternalIdentityView(
                    provider=identity.provider,
                    identifier=identity.identifier,
                    url=identity.url,
                )
                for identity in music.work.external_identities
            ],
            credits=_work_credit_views(music.work_credits, persons),
            classifications=sorted(
                (GenreSummary(id=str(genre.id), name=genre.content.canonical_name) for genre in music.genres),
                key=lambda item: item.name,
            ),
            related_works=sorted(
                (
                    RelatedWorkView(
                        relation_type=relation.relation_type,
                        work=SongSummary(
                            id=str(related_works[relation.target_work_id].id),
                            name=related_works[relation.target_work_id].canonical_title,
                        ),
                    )
                    for relation in outbound_relations
                    if relation.target_work_id in related_works
                ),
                key=lambda item: (item.work.name, item.relation_type.value),
            ),
            lyrics_versions=[
                SongLyricsVersionView(
                    id=str(version.id),
                    language_tag=version.language_tag,
                    label=version.label,
                    usage_kind=version.usage_kind,
                    creation_method=version.creation_method,
                    body=disclosure.body,
                    body_unavailable_reason=disclosure.body_unavailable_reason,
                    credits=_work_credit_views(lyrics_credits_by_version.get(version.id, ()), persons),
                    relations=_lyrics_relation_views(
                        version.id,
                        lyrics_relations_by_version.get(version.id, ()),
                        related_lyrics_versions,
                    ),
                )
                for version, disclosure in zip(music.lyrics_versions, body_disclosures, strict=True)
            ],
            recording_genres=recording_genres_view,
            recordings=recordings_view,
        )


def _work_credit_views(
    source_credits: Collection[WorkCredit] | Collection[LyricsVersionCredit],
    persons: dict[UUID, Person],
) -> list[SongWorkCreditView]:
    views: list[SongWorkCreditView] = []
    for credit in source_credits:
        person = persons.get(credit.person_id)
        if person is None:
            continue
        views.append(
            SongWorkCreditView(
                person=PerformerSummary(id=str(person.id), name=person.canonical_name),
                role=credit.role,
                credited_as=credit.credited_as,
            ),
        )
    views.sort(key=lambda item: (item.role.value, item.person.name))
    return views


def _lyrics_relation_views(
    version_id: UUID,
    relations: Collection[LyricsVersionRelation],
    versions: dict[UUID, LyricsVersion],
) -> list[LyricsVersionRelationView]:
    views: list[LyricsVersionRelationView] = []
    for relation in relations:
        other_id = _other_lyrics_version_id(relation, version_id)
        other_version = versions.get(other_id)
        if other_version is None:
            continue
        views.append(
            LyricsVersionRelationView(
                relation_type=relation.relation_type,
                version=LyricsVersionSummary(
                    id=str(other_version.id),
                    language_tag=other_version.language_tag,
                    label=other_version.label,
                ),
            ),
        )
    views.sort(key=lambda item: (item.relation_type.value, item.version.language_tag, item.version.label or ""))
    return views


def _other_lyrics_version_id(relation: LyricsVersionRelation, version_id: UUID) -> UUID:
    if relation.source_lyrics_version_id == version_id:
        return relation.target_lyrics_version_id
    return relation.source_lyrics_version_id


def _project_song_recordings(
    work_id: UUID,
    recordings: list[Recording],
    assignments_by_recording: dict[UUID, list[ClassificationAssignment]],
    genres: dict[UUID, Genre],
    persons: dict[UUID, Person],
    groups: dict[UUID, Group],
    origin_claims_by_recording: dict[UUID, list[RecordingOriginClaim]] | None = None,
) -> tuple[list[SongRecordingGenreFacet], list[SongRecordingSummary]]:
    claims_by_recording = origin_claims_by_recording or {}
    summaries: list[SongRecordingSummary] = []
    facet_recording_ids: defaultdict[UUID, set[UUID]] = defaultdict(set)

    for recording in recordings:
        work_usage = next(
            (usage for usage in recording.work_usages if usage.work_id == work_id),
            None,
        )
        if work_usage is None:
            continue

        primary_credits = project_primary_credits(recording, persons, groups)
        if not primary_credits:
            continue

        genre_concept_ids = {
            assignment.concept_id
            for assignment in assignments_by_recording.get(recording.id, ())
            if assignment.concept_id in genres
        }
        summaries.append(
            SongRecordingSummary(
                id=str(recording.id),
                title=recording.title,
                recorded_period=SongPeriodView.from_period(recording.recorded_period),
                first_release_date=None,
                primary_credits=primary_credits,
                genre_ids=sorted(str(concept_id) for concept_id in genre_concept_ids),
                work_usage_kind=work_usage.usage_kind,
                origin_badges=origin_badge_values(claims_by_recording.get(recording.id, ())),
            )
        )
        if work_usage.is_complete or work_usage.is_partial:
            for concept_id in genre_concept_ids:
                facet_recording_ids[concept_id].add(recording.id)

    summaries.sort(
        key=lambda item: (
            item.recorded_period.start is None,
            item.first_release_date is None,
            item.recorded_period.start.year if item.recorded_period.start is not None else 0,
            item.title.casefold(),
            item.id,
        )
    )
    return (
        sorted(
            (
                SongRecordingGenreFacet(
                    genre=GenreSummary(str(genre_id), genres[genre_id].content.canonical_name),
                    recording_count=len(recording_ids),
                )
                for genre_id, recording_ids in facet_recording_ids.items()
            ),
            key=lambda item: item.genre.name,
        ),
        summaries,
    )
