from typing import TypedDict
from uuid import UUID

from sqlalchemy import CheckConstraint, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from roots_of_rhythm.infrastructure.service_columns import ServiceColumnsMixin
from roots_of_rhythm.people_catalog.domain.enums import EditorialStatus, TemporalPrecision
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_64, TEXT_1024

# Retained for migration 0005 compatibility; current metadata no longer creates this index.
PERSON_NAME_UNIQUE_CONSTRAINT = "uq_persons_canonical_name_ci"
EDITORIAL_STATUS_CHECK = f"editorial_status IN ({', '.join(repr(status.value) for status in EditorialStatus)})"
TEMPORAL_PRECISION_CHECK = (
    "({year_column} IS NULL AND {precision_column} IS NULL) OR "
    "({year_column} IS NOT NULL AND {precision_column} IN "
    f"({', '.join(repr(precision.value) for precision in TemporalPrecision)}))"
)


class ExternalIdentityData(TypedDict):
    provider: str
    identifier: str
    url: str | None


class PeopleCatalogBase(DeclarativeBase):
    pass


class PersonRecord(ServiceColumnsMixin, PeopleCatalogBase):
    __tablename__ = "persons"
    __table_args__ = (
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_persons_editorial_status"),
        CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column="birth_year",
                precision_column="birth_precision",
            ),
            name="ck_persons_birth_date",
        ),
        CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column="death_year",
                precision_column="death_precision",
            ),
            name="ck_persons_death_date",
        ),
        CheckConstraint(
            "birth_year IS NULL OR death_year IS NULL OR birth_year <= death_year",
            name="ck_persons_birth_before_death",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(TEXT_64), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default="[]")
    biography: Mapped[str | None] = mapped_column(String(TEXT_1024))
    birth_year: Mapped[int | None]
    birth_precision: Mapped[str | None] = mapped_column(String(TEXT_32))
    death_year: Mapped[int | None]
    death_precision: Mapped[str | None] = mapped_column(String(TEXT_32))
    external_identities: Mapped[list[ExternalIdentityData]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
    )


Index("ix_persons_editorial_status", PersonRecord.editorial_status)
