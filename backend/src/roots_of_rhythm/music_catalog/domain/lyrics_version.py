from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import msgspec

from roots_of_rhythm.music_catalog.domain.enums import EditorialStatus, LyricsCreationMethod, LyricsUsageKind
from roots_of_rhythm.music_catalog.domain.errors import LyricsVersionPublicationError, MusicCatalogDomainError

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.domain.value_objects import LyricsVersionContent


class LyricsVersion(msgspec.Struct, frozen=True):
    id: UUID
    work_id: UUID
    source_version_id: UUID
    language_tag: str
    usage_kind: LyricsUsageKind
    creation_method: LyricsCreationMethod
    label: str | None = None
    body: str | None = None
    provenance: str | None = None
    editorial_status: EditorialStatus = EditorialStatus.DRAFT

    @classmethod
    def create(
        cls,
        version_id: UUID,
        work_id: UUID,
        source_version_id: UUID,
        content: LyricsVersionContent,
        *,
        editorial_status: EditorialStatus = EditorialStatus.DRAFT,
    ) -> "LyricsVersion":
        return cls(
            id=version_id,
            work_id=work_id,
            source_version_id=source_version_id,
            language_tag=content.language_tag,
            usage_kind=content.usage_kind,
            creation_method=content.creation_method,
            label=content.label,
            body=content.body,
            provenance=content.provenance,
            editorial_status=editorial_status,
        )

    def replace_content(self, content: LyricsVersionContent) -> "LyricsVersion":
        if content.usage_kind is not self.usage_kind:
            raise MusicCatalogDomainError("LyricsVersionContent usage_kind must match the version usage_kind")
        if content.creation_method is not self.creation_method:
            raise MusicCatalogDomainError("LyricsVersionContent creation_method must match the version creation_method")
        return LyricsVersion(
            id=self.id,
            work_id=self.work_id,
            source_version_id=self.source_version_id,
            language_tag=content.language_tag,
            usage_kind=self.usage_kind,
            creation_method=self.creation_method,
            label=content.label,
            body=content.body,
            provenance=content.provenance,
            editorial_status=self.editorial_status,
        )

    def submit_for_review(self) -> "LyricsVersion":
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> "LyricsVersion":
        if self.creation_method is LyricsCreationMethod.MACHINE_TRANSLATION and self.editorial_status not in {
            EditorialStatus.IN_REVIEW,
            EditorialStatus.PUBLISHED,
        }:
            raise LyricsVersionPublicationError(("editorial_status",))
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "LyricsVersion":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "LyricsVersion":
        return LyricsVersion(
            id=self.id,
            work_id=self.work_id,
            source_version_id=self.source_version_id,
            language_tag=self.language_tag,
            usage_kind=self.usage_kind,
            creation_method=self.creation_method,
            label=self.label,
            body=self.body,
            provenance=self.provenance,
            editorial_status=status,
        )
