from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.music_catalog.application.ports import (
    LyricsVersionRelationRepository,
    LyricsVersionRepository,
)
from roots_of_rhythm.music_catalog.domain import LyricsUsageKind
from roots_of_rhythm.music_catalog.public.recording_lyrics_reader import (
    RecordingLyricsProjection,
    RecordingLyricsSelection,
)

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.domain import LyricsVersion, Recording

type LyricsRepositoryFactory = Callable[[Transaction], LyricsVersionRepository]
type LyricsRelationRepositoryFactory = Callable[[Transaction], LyricsVersionRelationRepository]


class RecordingLyricsReadService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        lyrics_repository_factory: LyricsRepositoryFactory,
        lyrics_relation_repository_factory: LyricsRelationRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._lyrics_repository_factory = lyrics_repository_factory
        self._lyrics_relation_repository_factory = lyrics_relation_repository_factory

    async def get(self, recording: Recording) -> RecordingLyricsProjection:
        async with self._transaction_scope() as transaction:
            lyrics_repository = self._lyrics_repository_factory(transaction)
            lyrics_relation_repository = self._lyrics_relation_repository_factory(transaction)

            explicit = await lyrics_repository.get_published_by_ids(
                tuple(usage.lyrics_version_id for usage in recording.lyrics_usages)
            )
            selected: list[tuple[LyricsVersion, int | None, bool]] = [
                (explicit[usage.lyrics_version_id], usage.position, True)
                for usage in recording.lyrics_usages
                if usage.lyrics_version_id in explicit
            ]
            if not selected:
                versions_by_work = await lyrics_repository.list_published_for_works(
                    tuple(usage.work_id for usage in recording.work_usages)
                )
                for work_usage in recording.work_usages:
                    versions = versions_by_work.get(work_usage.work_id, ())
                    if version := next((item for item in versions if item.is_performable), None):
                        selected = [(version, None, False)]
                        break

            relations = await lyrics_relation_repository.list_published_for_versions(
                [version.id for version, _position, _confirmed in selected]
            )
            translation_ids = {
                relation.source_lyrics_version_id
                for version, _position, _confirmed in selected
                for relation in relations.get(version.id, ())
                if relation.is_translation_of and relation.target_lyrics_version_id == version.id
            }
            translations = await lyrics_repository.get_published_by_ids(translation_ids)

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
                                if relation.is_translation_of
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
