from uuid import UUID

import msgspec

from roots_of_rhythm.music_catalog.domain.enums import EditorialStatus, LyricsVersionRelationType
from roots_of_rhythm.music_catalog.domain.errors import (
    LyricsVersionRelationPublicationError,
    LyricsVersionRelationSelfReferenceError,
    MusicCatalogDomainError,
)
from roots_of_rhythm.music_catalog.domain.value_objects import LyricsVersionRelationContent


class LyricsVersionRelation(msgspec.Struct, frozen=True):
    id: UUID
    source_lyrics_version_id: UUID
    target_lyrics_version_id: UUID
    relation_type: LyricsVersionRelationType
    provenance: str | None = None
    editorial_status: EditorialStatus = EditorialStatus.DRAFT

    @classmethod
    def create(
        cls,
        relation_id: UUID,
        source_lyrics_version_id: UUID,
        target_lyrics_version_id: UUID,
        relation_type: LyricsVersionRelationType,
        content: LyricsVersionRelationContent | None = None,
        *,
        editorial_status: EditorialStatus = EditorialStatus.DRAFT,
    ) -> "LyricsVersionRelation":
        if source_lyrics_version_id == target_lyrics_version_id:
            raise LyricsVersionRelationSelfReferenceError()
        normalized = content or LyricsVersionRelationContent.create(relation_type=relation_type)
        if normalized.relation_type is not relation_type:
            raise MusicCatalogDomainError(
                "LyricsVersionRelationContent relation_type must match the provided relation_type"
            )
        return cls(
            id=relation_id,
            source_lyrics_version_id=source_lyrics_version_id,
            target_lyrics_version_id=target_lyrics_version_id,
            relation_type=relation_type,
            provenance=normalized.provenance,
            editorial_status=editorial_status,
        )

    def replace_content(self, content: LyricsVersionRelationContent) -> "LyricsVersionRelation":
        if content.relation_type is not self.relation_type:
            raise MusicCatalogDomainError("LyricsVersionRelationContent relation_type must match the relation type")
        return LyricsVersionRelation(
            id=self.id,
            source_lyrics_version_id=self.source_lyrics_version_id,
            target_lyrics_version_id=self.target_lyrics_version_id,
            relation_type=self.relation_type,
            provenance=content.provenance,
            editorial_status=self.editorial_status,
        )

    def submit_for_review(self) -> "LyricsVersionRelation":
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> "LyricsVersionRelation":
        if self.provenance is None:
            raise LyricsVersionRelationPublicationError(("provenance",))
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "LyricsVersionRelation":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "LyricsVersionRelation":
        return LyricsVersionRelation(
            id=self.id,
            source_lyrics_version_id=self.source_lyrics_version_id,
            target_lyrics_version_id=self.target_lyrics_version_id,
            relation_type=self.relation_type,
            provenance=self.provenance,
            editorial_status=status,
        )
