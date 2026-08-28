from uuid import UUID

from sqlalchemy import CheckConstraint, Index, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from roots_of_rhythm.infrastructure.service_columns import ServiceColumnsMixin
from roots_of_rhythm.music_catalog.infrastructure.models.base import (
    EDITORIAL_STATUS_CHECK,
    LYRICS_CREATION_METHOD_CHECK,
    LYRICS_USAGE_KIND_CHECK,
    LYRICS_VERSION_CREDIT_UNIQUE_CONSTRAINT,
    LYRICS_VERSION_RELATION_TYPE_CHECK,
    LYRICS_VERSION_RELATION_UNIQUE_CONSTRAINT,
    LYRICS_VERSION_UNIQUE_CONSTRAINT,
    WORK_CREDIT_ROLE_CHECK,
    MusicCatalogBase,
)
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_64, TEXT_1024, TEXT_4096


class LyricsVersionRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "lyrics_versions"
    __table_args__ = (
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_lyrics_versions_editorial_status"),
        CheckConstraint(LYRICS_USAGE_KIND_CHECK, name="ck_lyrics_versions_usage_kind"),
        CheckConstraint(LYRICS_CREATION_METHOD_CHECK, name="ck_lyrics_versions_creation_method"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    work_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    source_version_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    language_tag: Mapped[str] = mapped_column(String(TEXT_64), nullable=False)
    usage_kind: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    creation_method: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    label: Mapped[str | None] = mapped_column(String(TEXT_64))
    body: Mapped[str | None] = mapped_column(String(TEXT_4096))
    provenance: Mapped[str | None] = mapped_column(String(TEXT_1024))
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)


Index(
    LYRICS_VERSION_UNIQUE_CONSTRAINT,
    LyricsVersionRecord.work_id,
    LyricsVersionRecord.language_tag,
    LyricsVersionRecord.usage_kind,
    func.coalesce(LyricsVersionRecord.label, ""),
    unique=True,
    postgresql_where=LyricsVersionRecord.deleted.is_(False),
)
Index("ix_lyrics_versions_work_id", LyricsVersionRecord.work_id)
Index("ix_lyrics_versions_source_version_id", LyricsVersionRecord.source_version_id)


class LyricsVersionCreditRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "lyrics_version_credits"
    __table_args__ = (
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_lyrics_version_credits_editorial_status"),
        CheckConstraint(WORK_CREDIT_ROLE_CHECK, name="ck_lyrics_version_credits_role"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    lyrics_version_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    person_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    credited_as: Mapped[str | None] = mapped_column(String(TEXT_64))
    provenance: Mapped[str | None] = mapped_column(String(TEXT_1024))
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)


Index(
    LYRICS_VERSION_CREDIT_UNIQUE_CONSTRAINT,
    LyricsVersionCreditRecord.lyrics_version_id,
    LyricsVersionCreditRecord.person_id,
    LyricsVersionCreditRecord.role,
    unique=True,
    postgresql_where=LyricsVersionCreditRecord.deleted.is_(False),
)
Index("ix_lyrics_version_credits_lyrics_version_id", LyricsVersionCreditRecord.lyrics_version_id)


class LyricsVersionRelationRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "lyrics_version_relations"
    __table_args__ = (
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_lyrics_version_relations_editorial_status"),
        CheckConstraint(LYRICS_VERSION_RELATION_TYPE_CHECK, name="ck_lyrics_version_relations_relation_type"),
        CheckConstraint(
            "source_lyrics_version_id <> target_lyrics_version_id",
            name="ck_lyrics_version_relations_no_self_reference",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    source_lyrics_version_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    target_lyrics_version_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    provenance: Mapped[str | None] = mapped_column(String(TEXT_1024))
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)


Index(
    LYRICS_VERSION_RELATION_UNIQUE_CONSTRAINT,
    LyricsVersionRelationRecord.source_lyrics_version_id,
    LyricsVersionRelationRecord.target_lyrics_version_id,
    LyricsVersionRelationRecord.relation_type,
    unique=True,
    postgresql_where=LyricsVersionRelationRecord.deleted.is_(False),
)
Index("ix_lyrics_version_relations_source", LyricsVersionRelationRecord.source_lyrics_version_id)
Index("ix_lyrics_version_relations_target", LyricsVersionRelationRecord.target_lyrics_version_id)
