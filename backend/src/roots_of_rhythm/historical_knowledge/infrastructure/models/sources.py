from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from roots_of_rhythm.historical_knowledge.domain.enums import SourceAccessPolicy
from roots_of_rhythm.historical_knowledge.infrastructure.models.base import (
    FRAGMENT_REVIEW_CHECK,
    SOURCE_ACCESS_POLICY_CHECK,
    HistoricalKnowledgeBase,
)
from roots_of_rhythm.infrastructure.service_columns import ServiceColumnsMixin
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_64, TEXT_1024, TEXT_2048


class SourceRecord(ServiceColumnsMixin, HistoricalKnowledgeBase):
    __tablename__ = "sources"
    __table_args__ = (CheckConstraint(SOURCE_ACCESS_POLICY_CHECK, name="ck_sources_access_policy"),)

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(TEXT_64), nullable=False)
    author: Mapped[str | None] = mapped_column(String(TEXT_64))
    responsible_organization: Mapped[str | None] = mapped_column(String(TEXT_64))
    publication: Mapped[str | None] = mapped_column(String(TEXT_64))
    publication_date: Mapped[str | None] = mapped_column(String(TEXT_64))
    external_url: Mapped[str | None] = mapped_column(String(TEXT_2048))
    access_policy: Mapped[str] = mapped_column(
        String(TEXT_32),
        nullable=False,
        server_default=SourceAccessPolicy.WITHHOLD_PUBLIC_BODY.value,
    )


class SourceVersionRecord(ServiceColumnsMixin, HistoricalKnowledgeBase):
    __tablename__ = "source_versions"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    source_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sources.id"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(TEXT_64), nullable=False)


class SourceFragmentRecord(ServiceColumnsMixin, HistoricalKnowledgeBase):
    __tablename__ = "source_fragments"
    __table_args__ = (CheckConstraint(FRAGMENT_REVIEW_CHECK, name="ck_source_fragments_review_status"),)

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    source_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("source_versions.id"),
        nullable=False,
    )
    review_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    locator_text: Mapped[str | None] = mapped_column(String(TEXT_1024))
    external_url: Mapped[str | None] = mapped_column(String(TEXT_2048))
