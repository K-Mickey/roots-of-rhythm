from uuid import UUID

from sqlalchemy import CheckConstraint, Index, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from roots_of_rhythm.infrastructure.service_columns import ServiceColumnsMixin
from roots_of_rhythm.music_catalog.domain.enums import (
    ClassificationKind,
    ClassificationTargetKind,
    EditorialStatus,
    EvidenceStatus,
    TemporalPrecision,
)
from roots_of_rhythm.music_catalog.domain.value_objects import LONG_TEXT_MAX_LENGTH, SHORT_TEXT_MAX_LENGTH

CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT = "uq_classification_concepts_kind_canonical_name_ci"

KIND_CHECK = f"kind IN ({', '.join(repr(kind.value) for kind in ClassificationKind)})"
TARGET_KIND_CHECK = f"target_kind IN ({', '.join(repr(kind.value) for kind in ClassificationTargetKind)})"
EDITORIAL_STATUS_CHECK = f"editorial_status IN ({', '.join(repr(status.value) for status in EditorialStatus)})"
EVIDENCE_STATUS_CHECK = f"evidence_status IN ({', '.join(repr(status.value) for status in EvidenceStatus)})"
CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT = "uq_classification_assignments_target_concept"
TEMPORAL_PRECISION_CHECK = (
    "({year_column} IS NULL AND {precision_column} IS NULL) OR "
    "({year_column} IS NOT NULL AND {precision_column} IN "
    f"({', '.join(repr(precision.value) for precision in TemporalPrecision)}))"
)
PERIOD_START_YEAR_COLUMN = "period_start_year"
PERIOD_START_PRECISION_COLUMN = "period_start_precision"
PERIOD_END_YEAR_COLUMN = "period_end_year"
PERIOD_END_PRECISION_COLUMN = "period_end_precision"


class MusicCatalogBase(DeclarativeBase):
    pass


class ClassificationConceptRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "classification_concepts"
    __table_args__ = (
        CheckConstraint(KIND_CHECK, name="ck_classification_concepts_kind"),
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_classification_concepts_editorial_status"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    editorial_status: Mapped[str] = mapped_column(String(32), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(SHORT_TEXT_MAX_LENGTH), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String(SHORT_TEXT_MAX_LENGTH)), nullable=False)
    definition: Mapped[str | None] = mapped_column(String(LONG_TEXT_MAX_LENGTH))
    boundaries: Mapped[str | None] = mapped_column(String(LONG_TEXT_MAX_LENGTH))
    period_label: Mapped[str | None] = mapped_column(String(SHORT_TEXT_MAX_LENGTH))
    period_start_year: Mapped[int | None]
    period_start_precision: Mapped[str | None] = mapped_column(String(32))
    period_end_year: Mapped[int | None]
    period_end_precision: Mapped[str | None] = mapped_column(String(32))
    geography_summary: Mapped[str | None] = mapped_column(String(SHORT_TEXT_MAX_LENGTH))
    historical_context: Mapped[str | None] = mapped_column(String(LONG_TEXT_MAX_LENGTH))
    formation: Mapped[str | None] = mapped_column(String(LONG_TEXT_MAX_LENGTH))
    characteristic_features: Mapped[list[str]] = mapped_column(
        ARRAY(String(SHORT_TEXT_MAX_LENGTH)),
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
    target_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    concept_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    explanation: Mapped[str | None] = mapped_column(String(LONG_TEXT_MAX_LENGTH))
    claim_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    provenance: Mapped[str | None] = mapped_column(String(LONG_TEXT_MAX_LENGTH))
    evidence_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=EvidenceStatus.UNVERIFIED.value,
    )
    editorial_status: Mapped[str] = mapped_column(String(32), nullable=False)


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


class GroupRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "groups"
    __table_args__ = (
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_groups_editorial_status"),
        CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_START_YEAR_COLUMN,
                precision_column=PERIOD_START_PRECISION_COLUMN,
            ),
            name="ck_groups_period_start",
        ),
        CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_END_YEAR_COLUMN,
                precision_column=PERIOD_END_PRECISION_COLUMN,
            ),
            name="ck_groups_period_end",
        ),
        CheckConstraint(
            "period_start_year IS NULL OR period_end_year IS NULL OR period_start_year <= period_end_year",
            name="ck_groups_period_order",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    editorial_status: Mapped[str] = mapped_column(String(32), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(SHORT_TEXT_MAX_LENGTH), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String(SHORT_TEXT_MAX_LENGTH)), nullable=False)
    description: Mapped[str | None] = mapped_column(String(LONG_TEXT_MAX_LENGTH))
    period_start_year: Mapped[int | None]
    period_start_precision: Mapped[str | None] = mapped_column(String(32))
    period_end_year: Mapped[int | None]
    period_end_precision: Mapped[str | None] = mapped_column(String(32))


Index("ix_groups_editorial_status", GroupRecord.editorial_status)


class GroupMembershipRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "group_memberships"
    __table_args__ = (
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_group_memberships_editorial_status"),
        CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_START_YEAR_COLUMN,
                precision_column=PERIOD_START_PRECISION_COLUMN,
            ),
            name="ck_group_memberships_period_start",
        ),
        CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_END_YEAR_COLUMN,
                precision_column=PERIOD_END_PRECISION_COLUMN,
            ),
            name="ck_group_memberships_period_end",
        ),
        CheckConstraint(
            "period_start_year IS NULL OR period_end_year IS NULL OR period_start_year <= period_end_year",
            name="ck_group_memberships_period_order",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    person_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    group_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    editorial_status: Mapped[str] = mapped_column(String(32), nullable=False)
    period_start_year: Mapped[int | None]
    period_start_precision: Mapped[str | None] = mapped_column(String(32))
    period_end_year: Mapped[int | None]
    period_end_precision: Mapped[str | None] = mapped_column(String(32))
    roles_or_instruments: Mapped[list[str]] = mapped_column(ARRAY(String(SHORT_TEXT_MAX_LENGTH)), nullable=False)
    provenance: Mapped[str | None] = mapped_column(String(LONG_TEXT_MAX_LENGTH))


Index("ix_group_memberships_group_id", GroupMembershipRecord.group_id)
Index("ix_group_memberships_person_id", GroupMembershipRecord.person_id)
