from uuid import UUID

from sqlalchemy import CheckConstraint, Index, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from roots_of_rhythm.infrastructure.service_columns import ServiceColumnsMixin
from roots_of_rhythm.music_catalog.domain.enums import ClassificationKind, EditorialStatus
from roots_of_rhythm.music_catalog.domain.value_objects import LONG_TEXT_MAX_LENGTH, SHORT_TEXT_MAX_LENGTH

CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT = "uq_classification_concepts_kind_canonical_name_ci"

KIND_CHECK = f"kind IN ({', '.join(repr(kind.value) for kind in ClassificationKind)})"
EDITORIAL_STATUS_CHECK = f"editorial_status IN ({', '.join(repr(status.value) for status in EditorialStatus)})"


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
