from uuid import UUID

import msgspec

from roots_of_rhythm.music_catalog.domain.enums import EditorialStatus, WorkCreditRole
from roots_of_rhythm.music_catalog.domain.errors import MusicCatalogDomainError
from roots_of_rhythm.music_catalog.domain.value_objects import WorkCreditContent


class WorkCredit(msgspec.Struct, frozen=True):
    id: UUID
    work_id: UUID
    person_id: UUID
    role: WorkCreditRole
    credited_as: str | None = None
    provenance: str | None = None
    editorial_status: EditorialStatus = EditorialStatus.DRAFT

    @classmethod
    def create(
        cls,
        credit_id: UUID,
        work_id: UUID,
        person_id: UUID,
        role: WorkCreditRole,
        content: WorkCreditContent | None = None,
        *,
        editorial_status: EditorialStatus = EditorialStatus.DRAFT,
    ) -> "WorkCredit":
        normalized = content or WorkCreditContent.create(role=role)
        if normalized.role is not role:
            raise MusicCatalogDomainError("WorkCreditContent role must match the provided role")
        return cls(
            id=credit_id,
            work_id=work_id,
            person_id=person_id,
            role=role,
            credited_as=normalized.credited_as,
            provenance=normalized.provenance,
            editorial_status=editorial_status,
        )

    def replace_content(self, content: WorkCreditContent) -> "WorkCredit":
        if content.role is not self.role:
            raise MusicCatalogDomainError("WorkCreditContent role must match the credit role")
        return WorkCredit(
            id=self.id,
            work_id=self.work_id,
            person_id=self.person_id,
            role=self.role,
            credited_as=content.credited_as,
            provenance=content.provenance,
            editorial_status=self.editorial_status,
        )

    def submit_for_review(self) -> "WorkCredit":
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> "WorkCredit":
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "WorkCredit":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "WorkCredit":
        return WorkCredit(
            id=self.id,
            work_id=self.work_id,
            person_id=self.person_id,
            role=self.role,
            credited_as=self.credited_as,
            provenance=self.provenance,
            editorial_status=status,
        )
