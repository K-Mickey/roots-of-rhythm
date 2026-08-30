from typing import TYPE_CHECKING
from uuid import UUID, uuid7

import pytest

from roots_of_rhythm.discovery.application import RecordingLyricsProjectionQuery
from roots_of_rhythm.music_catalog.domain import (
    EditorialStatus,
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersion,
    LyricsVersionContent,
    LyricsVersionRelation,
    LyricsVersionRelationType,
    Recording,
    RecordingContent,
    RecordingLyricsUsage,
    RecordingWorkUsage,
    RecordingWorkUsageKind,
)
from tests.music_catalog.fakes import FakeLyricsVersionRepository, FakeMusicCatalogUnitOfWork

if TYPE_CHECKING:
    from collections.abc import Collection


class SpyLyricsVersionRepository(FakeLyricsVersionRepository):
    def __init__(self, versions: dict[UUID, LyricsVersion]) -> None:
        super().__init__(versions)
        self.published_for_works_calls: list[set[UUID]] = []

    async def list_published_for_works(self, work_ids: "Collection[UUID]") -> dict[UUID, list[LyricsVersion]]:
        self.published_for_works_calls.append(set(work_ids))
        return await super().list_published_for_works(work_ids)


def _version(
    work_id: UUID,
    language: str,
    usage_kind: LyricsUsageKind,
    creation_method: LyricsCreationMethod,
    status: EditorialStatus = EditorialStatus.PUBLISHED,
) -> LyricsVersion:
    return LyricsVersion.create(
        uuid7(),
        work_id,
        uuid7(),
        LyricsVersionContent.create(
            language_tag=language,
            usage_kind=usage_kind,
            creation_method=creation_method,
        ),
        editorial_status=status,
    )


@pytest.mark.asyncio
async def test_recording_lyrics_projection_returns_reading_translations_and_fallback() -> None:
    first_work_id = uuid7()
    work_id = uuid7()
    first_work_reading = _version(
        first_work_id,
        "fr",
        LyricsUsageKind.READING_TRANSLATION,
        LyricsCreationMethod.HUMAN_TRANSLATION,
    )
    sounding = _version(work_id, "en", LyricsUsageKind.PERFORMABLE, LyricsCreationMethod.ORIGINAL)
    machine = _version(
        work_id,
        "ru",
        LyricsUsageKind.READING_TRANSLATION,
        LyricsCreationMethod.MACHINE_TRANSLATION,
    )
    hidden = _version(
        work_id,
        "de",
        LyricsUsageKind.READING_TRANSLATION,
        LyricsCreationMethod.HUMAN_TRANSLATION,
        EditorialStatus.DRAFT,
    )
    relations = {
        relation.id: relation
        for relation in (
            LyricsVersionRelation.create(
                uuid7(),
                translation.id,
                sounding.id,
                LyricsVersionRelationType.TRANSLATION_OF,
                editorial_status=EditorialStatus.PUBLISHED,
            )
            for translation in (machine, hidden)
        )
    }
    versions = {version.id: version for version in (first_work_reading, sounding, machine, hidden)}
    uow = FakeMusicCatalogUnitOfWork({}, lyrics_versions=versions, lyrics_version_relations=relations)
    lyrics_versions = SpyLyricsVersionRepository(versions)
    uow.lyrics_versions = lyrics_versions
    query = RecordingLyricsProjectionQuery(lambda: uow)
    work_usage = RecordingWorkUsage.create(uuid7(), work_id, RecordingWorkUsageKind.COMPLETE)
    explicit = Recording.create(
        uuid7(),
        RecordingContent.create(
            "Take",
            work_usages=(work_usage,),
            lyrics_usages=(RecordingLyricsUsage.create(uuid7(), sounding.id),),
        ),
    )

    projection = await query.get(explicit)
    assert projection.items[0].confirmed_for_recording is True
    assert projection.items[0].reading_translations == (machine,)

    fallback = await query.get(
        Recording.create(
            uuid7(),
            RecordingContent.create(
                "Instrumental?",
                work_usages=(
                    RecordingWorkUsage.create(
                        uuid7(), first_work_id, RecordingWorkUsageKind.MEDLEY_COMPONENT, position=1
                    ),
                    RecordingWorkUsage.create(uuid7(), work_id, RecordingWorkUsageKind.MEDLEY_COMPONENT, position=2),
                ),
            ),
        )
    )
    assert fallback.items[0].version == sounding
    assert fallback.items[0].confirmed_for_recording is False
    assert lyrics_versions.published_for_works_calls == [{first_work_id, work_id}]
