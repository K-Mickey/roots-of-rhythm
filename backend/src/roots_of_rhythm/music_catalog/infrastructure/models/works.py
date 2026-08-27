from typing import TypedDict
from uuid import UUID

from sqlalchemy import CheckConstraint, Index, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from roots_of_rhythm.infrastructure.service_columns import ServiceColumnsMixin
from roots_of_rhythm.music_catalog.domain.enums import EvidenceStatus
from roots_of_rhythm.music_catalog.infrastructure.models.base import (
    EDITORIAL_STATUS_CHECK,
    EVIDENCE_STATUS_CHECK,
    PERIOD_END_PRECISION_COLUMN,
    PERIOD_END_YEAR_COLUMN,
    PERIOD_START_PRECISION_COLUMN,
    PERIOD_START_YEAR_COLUMN,
    TEMPORAL_PRECISION_CHECK,
    WORK_CREDIT_ROLE_CHECK,
    WORK_CREDIT_UNIQUE_CONSTRAINT,
    WORK_RELATION_TYPE_CHECK,
    WORK_RELATION_UNIQUE_CONSTRAINT,
    MusicCatalogBase,
)
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_64, TEXT_1024


class ExternalIdentityData(TypedDict):
    provider: str
    identifier: str
    url: str | None


class MusicalWorkRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "musical_works"
    __table_args__ = (
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_musical_works_editorial_status"),
        CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_START_YEAR_COLUMN,
                precision_column=PERIOD_START_PRECISION_COLUMN,
            ),
            name="ck_musical_works_period_start",
        ),
        CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_END_YEAR_COLUMN,
                precision_column=PERIOD_END_PRECISION_COLUMN,
            ),
            name="ck_musical_works_period_end",
        ),
        CheckConstraint(
            "period_start_year IS NULL OR period_end_year IS NULL OR period_start_year <= period_end_year",
            name="ck_musical_works_period_order",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    canonical_title: Mapped[str] = mapped_column(String(TEXT_64), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String(TEXT_64)), nullable=False)
    description: Mapped[str | None] = mapped_column(String(TEXT_1024))
    period_start_year: Mapped[int | None]
    period_start_precision: Mapped[str | None] = mapped_column(String(TEXT_32))
    period_end_year: Mapped[int | None]
    period_end_precision: Mapped[str | None] = mapped_column(String(TEXT_32))
    external_identities: Mapped[list[ExternalIdentityData]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
    )
    provenance: Mapped[str | None] = mapped_column(String(TEXT_1024))


Index("ix_musical_works_editorial_status", MusicalWorkRecord.editorial_status)


class WorkCreditRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "work_credits"
    __table_args__ = (
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_work_credits_editorial_status"),
        CheckConstraint(WORK_CREDIT_ROLE_CHECK, name="ck_work_credits_role"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    work_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    person_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    credited_as: Mapped[str | None] = mapped_column(String(TEXT_64))
    provenance: Mapped[str | None] = mapped_column(String(TEXT_1024))
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)


Index(
    WORK_CREDIT_UNIQUE_CONSTRAINT,
    WorkCreditRecord.work_id,
    WorkCreditRecord.person_id,
    WorkCreditRecord.role,
    unique=True,
    postgresql_where=WorkCreditRecord.deleted.is_(False),
)
Index("ix_work_credits_work_id", WorkCreditRecord.work_id)
Index("ix_work_credits_person_id", WorkCreditRecord.person_id)


class WorkRelationRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "work_relations"
    __table_args__ = (
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_work_relations_editorial_status"),
        CheckConstraint(EVIDENCE_STATUS_CHECK, name="ck_work_relations_evidence_status"),
        CheckConstraint(WORK_RELATION_TYPE_CHECK, name="ck_work_relations_relation_type"),
        CheckConstraint("source_work_id <> target_work_id", name="ck_work_relations_no_self_reference"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    source_work_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    target_work_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    provenance: Mapped[str | None] = mapped_column(String(TEXT_1024))
    evidence_status: Mapped[str] = mapped_column(
        String(TEXT_32),
        nullable=False,
        server_default=EvidenceStatus.UNVERIFIED.value,
    )
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)


Index(
    WORK_RELATION_UNIQUE_CONSTRAINT,
    WorkRelationRecord.source_work_id,
    WorkRelationRecord.target_work_id,
    WorkRelationRecord.relation_type,
    unique=True,
    postgresql_where=WorkRelationRecord.deleted.is_(False),
)
Index("ix_work_relations_source_work_id", WorkRelationRecord.source_work_id)
Index("ix_work_relations_target_work_id", WorkRelationRecord.target_work_id)
