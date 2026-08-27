from uuid import UUID

from sqlalchemy import CheckConstraint, Index, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from roots_of_rhythm.infrastructure.service_columns import ServiceColumnsMixin
from roots_of_rhythm.music_catalog.domain.enums import EvidenceStatus
from roots_of_rhythm.music_catalog.infrastructure.models.base import (
    CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT,
    CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT,
    EDITORIAL_STATUS_CHECK,
    EVIDENCE_STATUS_CHECK,
    KIND_CHECK,
    TARGET_KIND_CHECK,
    MusicCatalogBase,
)
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_64, TEXT_1024


class ClassificationConceptRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "classification_concepts"
    __table_args__ = (
        CheckConstraint(KIND_CHECK, name="ck_classification_concepts_kind"),
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_classification_concepts_editorial_status"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    kind: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(TEXT_64), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String(TEXT_64)), nullable=False)
    definition: Mapped[str | None] = mapped_column(String(TEXT_1024))
    boundaries: Mapped[str | None] = mapped_column(String(TEXT_1024))
    period_label: Mapped[str | None] = mapped_column(String(TEXT_64))
    period_start_year: Mapped[int | None]
    period_start_precision: Mapped[str | None] = mapped_column(String(TEXT_32))
    period_end_year: Mapped[int | None]
    period_end_precision: Mapped[str | None] = mapped_column(String(TEXT_32))
    geography_summary: Mapped[str | None] = mapped_column(String(TEXT_64))
    historical_context: Mapped[str | None] = mapped_column(String(TEXT_1024))
    formation: Mapped[str | None] = mapped_column(String(TEXT_1024))
    characteristic_features: Mapped[list[str]] = mapped_column(
        ARRAY(String(TEXT_64)),
        nullable=False,
    )
    primary_image_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))


Index(
    CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT,
    ClassificationConceptRecord.kind,
    func.lower(ClassificationConceptRecord.canonical_name),
    unique=True,
    postgresql_where=ClassificationConceptRecord.deleted.is_(False),
)
Index(
    "ix_classification_concepts_kind_editorial_status",
    ClassificationConceptRecord.kind,
    ClassificationConceptRecord.editorial_status,
)


class ClassificationAssignmentRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "classification_assignments"
    __table_args__ = (
        CheckConstraint(TARGET_KIND_CHECK, name="ck_classification_assignments_target_kind"),
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_classification_assignments_editorial_status"),
        CheckConstraint(EVIDENCE_STATUS_CHECK, name="ck_classification_assignments_evidence_status"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    target_kind: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    target_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    concept_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    explanation: Mapped[str | None] = mapped_column(String(TEXT_1024))
    claim_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    provenance: Mapped[str | None] = mapped_column(String(TEXT_1024))
    evidence_status: Mapped[str] = mapped_column(
        String(TEXT_32),
        nullable=False,
        server_default=EvidenceStatus.UNVERIFIED.value,
    )
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)


Index(
    CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT,
    ClassificationAssignmentRecord.target_kind,
    ClassificationAssignmentRecord.target_id,
    ClassificationAssignmentRecord.concept_id,
    unique=True,
    postgresql_where=ClassificationAssignmentRecord.deleted.is_(False),
)
Index(
    "ix_classification_assignments_target",
    ClassificationAssignmentRecord.target_kind,
    ClassificationAssignmentRecord.target_id,
)
