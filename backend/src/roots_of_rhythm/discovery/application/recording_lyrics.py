from collections.abc import Callable

import msgspec

from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
from roots_of_rhythm.music_catalog.domain import (
    LyricsUsageKind,
    LyricsVersion,
    LyricsVersionRelationType,
    Recording,
)

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


class RecordingLyricsSelection(msgspec.Struct, frozen=True):
    version: LyricsVersion
    position: int | None
    confirmed_for_recording: bool
    reading_translations: tuple[LyricsVersion, ...] = ()


class RecordingLyricsProjection(msgspec.Struct, frozen=True):
    items: tuple[RecordingLyricsSelection, ...] = ()


class RecordingLyricsProjectionQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get(self, recording: Recording) -> RecordingLyricsProjection:
        async with self._uow_factory() as uow:
            explicit = await uow.lyrics_versions.get_published_by_ids(
                [usage.lyrics_version_id for usage in recording.lyrics_usages]
            )
            selected: list[tuple[LyricsVersion, int | None, bool]] = [
                (explicit[usage.lyrics_version_id], usage.position, True)
                for usage in recording.lyrics_usages
                if usage.lyrics_version_id in explicit
            ]
            if not selected:
                versions_by_work = await uow.lyrics_versions.list_published_for_works(
                    [usage.work_id for usage in recording.work_usages],
                )
                for work_usage in recording.work_usages:
                    versions = versions_by_work.get(work_usage.work_id, ())
                    if version := next(
                        (item for item in versions if item.usage_kind is LyricsUsageKind.PERFORMABLE), None
                    ):
                        selected = [(version, None, False)]
                        break
            relations = await uow.lyrics_version_relations.list_published_for_versions(
                [version.id for version, _position, _confirmed in selected]
            )
            translation_ids = {
                relation.source_lyrics_version_id
                for version, _position, _confirmed in selected
                for relation in relations.get(version.id, ())
                if relation.relation_type is LyricsVersionRelationType.TRANSLATION_OF
                and relation.target_lyrics_version_id == version.id
            }
            translations = await uow.lyrics_versions.get_published_by_ids(translation_ids)

        return RecordingLyricsProjection(
            items=tuple(
                RecordingLyricsSelection(
                    version=version,
                    position=position,
                    confirmed_for_recording=confirmed,
                    reading_translations=tuple(
                        sorted(
                            (
                                translations[relation.source_lyrics_version_id]
                                for relation in relations.get(version.id, ())
                                if relation.relation_type is LyricsVersionRelationType.TRANSLATION_OF
                                and relation.target_lyrics_version_id == version.id
                                and relation.source_lyrics_version_id in translations
                                and translations[relation.source_lyrics_version_id].usage_kind
                                is LyricsUsageKind.READING_TRANSLATION
                            ),
                            key=lambda item: (item.language_tag, item.label or "", item.id),
                        )
                    ),
                )
                for version, position, confirmed in selected
            )
        )
