from uuid import UUID

import msgspec

from roots_of_rhythm.music_catalog.domain.enums import EditorialStatus, EvidenceStatus, WorkRelationType
from roots_of_rhythm.music_catalog.domain.errors import (
    MusicCatalogDomainError,
    WorkRelationPublicationError,
    WorkRelationSelfReferenceError,
)
from roots_of_rhythm.music_catalog.domain.value_objects import WorkRelationContent


class WorkRelation(msgspec.Struct, frozen=True):
    id: UUID
    source_work_id: UUID
    target_work_id: UUID
    relation_type: WorkRelationType
    provenance: str | None = None
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED
    editorial_status: EditorialStatus = EditorialStatus.DRAFT

    @classmethod
    def create(
        cls,
        relation_id: UUID,
        source_work_id: UUID,
        target_work_id: UUID,
        relation_type: WorkRelationType,
        content: WorkRelationContent | None = None,
        *,
        evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED,
        editorial_status: EditorialStatus = EditorialStatus.DRAFT,
    ) -> "WorkRelation":
        if source_work_id == target_work_id:
            raise WorkRelationSelfReferenceError()
        normalized = content or WorkRelationContent.create(relation_type=relation_type)
        if normalized.relation_type is not relation_type:
            raise MusicCatalogDomainError("WorkRelationContent relation_type must match the provided relation_type")
        return cls(
            id=relation_id,
            source_work_id=source_work_id,
            target_work_id=target_work_id,
            relation_type=relation_type,
            provenance=normalized.provenance,
            evidence_status=evidence_status,
            editorial_status=editorial_status,
        )

    def replace_content(
        self,
        content: WorkRelationContent,
        *,
        evidence_status: EvidenceStatus | None = None,
    ) -> "WorkRelation":
        if content.relation_type is not self.relation_type:
            raise MusicCatalogDomainError("WorkRelationContent relation_type must match the relation type")
        return WorkRelation(
            id=self.id,
            source_work_id=self.source_work_id,
            target_work_id=self.target_work_id,
            relation_type=self.relation_type,
            provenance=content.provenance,
            evidence_status=self.evidence_status if evidence_status is None else evidence_status,
            editorial_status=self.editorial_status,
        )

    def submit_for_review(self) -> "WorkRelation":
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> "WorkRelation":
        if self.provenance is None:
            raise WorkRelationPublicationError(("provenance",))
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> "WorkRelation":
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> "WorkRelation":
        return WorkRelation(
            id=self.id,
            source_work_id=self.source_work_id,
            target_work_id=self.target_work_id,
            relation_type=self.relation_type,
            provenance=self.provenance,
            evidence_status=self.evidence_status,
            editorial_status=status,
        )
