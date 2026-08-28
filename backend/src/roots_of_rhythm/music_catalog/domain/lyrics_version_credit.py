from uuid import UUID

import msgspec

from roots_of_rhythm.music_catalog.domain.enums import EditorialStatus, WorkCreditRole
from roots_of_rhythm.music_catalog.domain.errors import MusicCatalogDomainError
from roots_of_rhythm.music_catalog.domain.value_objects import LyricsVersionCreditContent


class LyricsVersionCredit(msgspec.Struct, frozen=True):
    id: UUID
    lyrics_version_id: UUID
    person_id: UUID
    role: WorkCreditRole
    credited_as: str | None = None
    provenance: str | None = None
    editorial_status: EditorialStatus = EditorialStatus.DRAFT

    @classmethod
    def create(
        cls,
        credit_id: UUID,
        lyrics_version_id: UUID,
        person_id: UUID,
        role: WorkCreditRole,
        content: LyricsVersionCreditContent | None = None,
        *,
        editorial_status: EditorialStatus = EditorialStatus.DRAFT,
    ) -> "LyricsVersionCredit":
        normalized = content or LyricsVersionCreditContent.create(role=role)
        if normalized.role is not role:
            raise MusicCatalogDomainError("LyricsVersionCreditContent role must match the provided role")
        return cls(
            id=credit_id,
            lyrics_version_id=lyrics_version_id,
            person_id=person_id,
            role=role,
            credited_as=normalized.credited_as,
            provenance=normalized.provenance,
            editorial_status=editorial_status,
        )

    def replace_content(self, content: LyricsVersionCreditContent) -> "LyricsVersionCredit":
        if content.role is not self.role:
            raise MusicCatalogDomainError("LyricsVersionCreditContent role must match the credit role")
        return LyricsVersionCredit(
            id=self.id,
            lyrics_version_id=self.lyrics_version_id,
            person_id=self.person_id,
            role=self.role,
            credited_as=content.credited_as,
            provenance=content.provenance,
            editorial_status=self.editorial_status,
        )

    def submit_for_review(self) -> "LyricsVersionCredit":
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> "LyricsVersionCredit":
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "LyricsVersionCredit":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "LyricsVersionCredit":
        return LyricsVersionCredit(
            id=self.id,
            lyrics_version_id=self.lyrics_version_id,
            person_id=self.person_id,
            role=self.role,
            credited_as=self.credited_as,
            provenance=self.provenance,
            editorial_status=status,
        )
