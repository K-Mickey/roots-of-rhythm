from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from roots_of_rhythm.historical_knowledge.domain.enums import (
    EditorialStatus,
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    RelationType,
)
from roots_of_rhythm.historical_knowledge.domain.value_objects import (
    LONG_TEXT_MAX_LENGTH,
    SHORT_TEXT_MAX_LENGTH,
    URL_MAX_LENGTH,
)
from roots_of_rhythm.infrastructure.service_columns import ServiceColumnsMixin

RELATION_TYPE_CHECK = f"relation_type IN ({', '.join(repr(item.value) for item in RelationType)})"
EDITORIAL_STATUS_CHECK = f"editorial_status IN ({', '.join(repr(item.value) for item in EditorialStatus)})"
EVIDENCE_STATUS_CHECK = f"evidence_status IN ({', '.join(repr(item.value) for item in EvidenceStatus)})"
EVIDENCE_ROLE_CHECK = f"role IN ({', '.join(repr(item.value) for item in EvidenceRole)})"
FRAGMENT_REVIEW_CHECK = f"review_status IN ({', '.join(repr(item.value) for item in FragmentReviewStatus)})"
CLAIM_ENDPOINTS_UNIQUE_INDEX = "uq_genre_relation_claims_endpoints_type"


class HistoricalKnowledgeBase(DeclarativeBase):
    pass


class SourceRecord(ServiceColumnsMixin, HistoricalKnowledgeBase):
    __tablename__ = "sources"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(SHORT_TEXT_MAX_LENGTH), nullable=False)
    author: Mapped[str | None] = mapped_column(String(SHORT_TEXT_MAX_LENGTH))
    responsible_organization: Mapped[str | None] = mapped_column(String(SHORT_TEXT_MAX_LENGTH))
    publication: Mapped[str | None] = mapped_column(String(SHORT_TEXT_MAX_LENGTH))
    publication_date: Mapped[str | None] = mapped_column(String(SHORT_TEXT_MAX_LENGTH))
    external_url: Mapped[str | None] = mapped_column(String(URL_MAX_LENGTH))


class SourceVersionRecord(ServiceColumnsMixin, HistoricalKnowledgeBase):
    __tablename__ = "source_versions"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    source_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sources.id"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(SHORT_TEXT_MAX_LENGTH), nullable=False)


class SourceFragmentRecord(ServiceColumnsMixin, HistoricalKnowledgeBase):
    __tablename__ = "source_fragments"
    __table_args__ = (CheckConstraint(FRAGMENT_REVIEW_CHECK, name="ck_source_fragments_review_status"),)

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    source_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("source_versions.id"),
        nullable=False,
    )
    review_status: Mapped[str] = mapped_column(String(32), nullable=False)
    locator_text: Mapped[str | None] = mapped_column(String(LONG_TEXT_MAX_LENGTH))
    external_url: Mapped[str | None] = mapped_column(String(URL_MAX_LENGTH))


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
    relation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    editorial_status: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_status: Mapped[str] = mapped_column(String(32), nullable=False)
    explanation: Mapped[str | None] = mapped_column(String(LONG_TEXT_MAX_LENGTH))
    period_label: Mapped[str | None] = mapped_column(String(SHORT_TEXT_MAX_LENGTH))
    period_start_year: Mapped[int | None]
    period_start_precision: Mapped[str | None] = mapped_column(String(32))
    period_end_year: Mapped[int | None]
    period_end_precision: Mapped[str | None] = mapped_column(String(32))
    geography_summary: Mapped[str | None] = mapped_column(String(SHORT_TEXT_MAX_LENGTH))
    provenance_summary: Mapped[str | None] = mapped_column(String(LONG_TEXT_MAX_LENGTH))


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
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    locator_text: Mapped[str | None] = mapped_column(String(LONG_TEXT_MAX_LENGTH))
    external_url: Mapped[str | None] = mapped_column(String(URL_MAX_LENGTH))


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
