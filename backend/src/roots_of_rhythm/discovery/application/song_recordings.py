from collections import defaultdict
from typing import TYPE_CHECKING

from roots_of_rhythm.discovery.application.dto import (
    GenreSummary,
    SongPeriodView,
    SongRecordingGenreFacet,
    SongRecordingSummary,
)
from roots_of_rhythm.discovery.application.recording_credits import project_primary_credits
from roots_of_rhythm.historical_knowledge.domain import origin_badge_values
from roots_of_rhythm.music_catalog.domain import RecordingWorkUsageKind

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import RecordingOriginClaim
    from roots_of_rhythm.music_catalog.domain import ClassificationAssignment, Genre, Group, Recording
    from roots_of_rhythm.people_catalog.domain import Person


def project_song_recordings(
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
        usage_kind = next(
            (usage.usage_kind for usage in recording.work_usages if usage.work_id == work_id),
            None,
        )
        if usage_kind is None:
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
                work_usage_kind=usage_kind,
                origin_badges=origin_badge_values(claims_by_recording.get(recording.id, ())),
            )
        )
        if usage_kind is RecordingWorkUsageKind.COMPLETE or usage_kind is RecordingWorkUsageKind.PARTIAL:
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
