from uuid import UUID

import msgspec

from roots_of_rhythm.music_catalog.domain.enums import EditorialStatus
from roots_of_rhythm.music_catalog.domain.errors import MusicalWorkPublicationError
from roots_of_rhythm.music_catalog.domain.value_objects import ExistencePeriod, ExternalIdentity, WorkContent


class MusicalWork(msgspec.Struct, frozen=True):
    id: UUID
    canonical_title: str
    aliases: tuple[str, ...] = ()
    description: str | None = None
    period: ExistencePeriod | None = None
    external_identities: tuple[ExternalIdentity, ...] = ()
    provenance: str | None = None
    editorial_status: EditorialStatus = EditorialStatus.DRAFT

    @classmethod
    def create(
        cls,
        work_id: UUID,
        content: WorkContent,
        *,
        editorial_status: EditorialStatus = EditorialStatus.DRAFT,
    ) -> "MusicalWork":
        return cls(
            id=work_id,
            canonical_title=content.canonical_title,
            aliases=content.aliases,
            description=content.description,
            period=content.period,
            external_identities=content.external_identities,
            provenance=content.provenance,
            editorial_status=editorial_status,
        )

    def replace_content(self, content: WorkContent) -> "MusicalWork":
        return MusicalWork.create(self.id, content, editorial_status=self.editorial_status)

    def submit_for_review(self) -> "MusicalWork":
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> "MusicalWork":
        missing_fields: list[str] = []
        if not self.canonical_title:
            missing_fields.append("canonical_title")
        if not self.provenance:
            missing_fields.append("provenance")
        if missing_fields:
            raise MusicalWorkPublicationError(tuple(missing_fields))
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "MusicalWork":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "MusicalWork":
        return MusicalWork(
            id=self.id,
            canonical_title=self.canonical_title,
            aliases=self.aliases,
            description=self.description,
            period=self.period,
            external_identities=self.external_identities,
            provenance=self.provenance,
            editorial_status=status,
        )
