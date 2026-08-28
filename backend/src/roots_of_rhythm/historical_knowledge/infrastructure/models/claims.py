from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from roots_of_rhythm.historical_knowledge.infrastructure.models.base import (
    CLAIM_ENDPOINTS_UNIQUE_INDEX,
    EDITORIAL_STATUS_CHECK,
    EVIDENCE_ROLE_CHECK,
    EVIDENCE_STATUS_CHECK,
    RELATION_TYPE_CHECK,
    HistoricalKnowledgeBase,
)
from roots_of_rhythm.infrastructure.service_columns import ServiceColumnsMixin
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_64, TEXT_1024, TEXT_2048


class GenreRelationClaimRecord(ServiceColumnsMixin, HistoricalKnowledgeBase):
    __tablename__ = "genre_relation_claims"
    __table_args__ = (
        CheckConstraint(RELATION_TYPE_CHECK, name="ck_genre_relation_claims_relation_type"),
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_genre_relation_claims_editorial_status"),
        CheckConstraint(EVIDENCE_STATUS_CHECK, name="ck_genre_relation_claims_evidence_status"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    subject_genre_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    target_genre_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(TEXT_64), nullable=False)
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    evidence_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    explanation: Mapped[str | None] = mapped_column(String(TEXT_1024))
    period_label: Mapped[str | None] = mapped_column(String(TEXT_64))
    period_start_year: Mapped[int | None]
    period_start_precision: Mapped[str | None] = mapped_column(String(TEXT_32))
    period_end_year: Mapped[int | None]
    period_end_precision: Mapped[str | None] = mapped_column(String(TEXT_32))
    geography_summary: Mapped[str | None] = mapped_column(String(TEXT_64))
    provenance_summary: Mapped[str | None] = mapped_column(String(TEXT_1024))


class ClaimEvidenceReferenceRecord(ServiceColumnsMixin, HistoricalKnowledgeBase):
    __tablename__ = "claim_evidence_references"
    __table_args__ = (CheckConstraint(EVIDENCE_ROLE_CHECK, name="ck_claim_evidence_references_role"),)

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    claim_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("genre_relation_claims.id"),
        nullable=False,
    )
    source_fragment_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("source_fragments.id"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    locator_text: Mapped[str | None] = mapped_column(String(TEXT_1024))
    external_url: Mapped[str | None] = mapped_column(String(TEXT_2048))


Index(
    CLAIM_ENDPOINTS_UNIQUE_INDEX,
    GenreRelationClaimRecord.subject_genre_id,
    GenreRelationClaimRecord.target_genre_id,
    GenreRelationClaimRecord.relation_type,
    unique=True,
    postgresql_where=GenreRelationClaimRecord.deleted.is_(False),
)
Index(
    "ix_genre_relation_claims_subject_genre_id",
    GenreRelationClaimRecord.subject_genre_id,
)
Index(
    "ix_genre_relation_claims_target_genre_id",
    GenreRelationClaimRecord.target_genre_id,
)
Index(
    "ix_claim_evidence_references_claim_id",
    ClaimEvidenceReferenceRecord.claim_id,
)
