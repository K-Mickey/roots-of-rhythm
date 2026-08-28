from uuid import UUID

from sqlalchemy import CheckConstraint, Index, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from roots_of_rhythm.infrastructure.service_columns import ServiceColumnsMixin
from roots_of_rhythm.music_catalog.infrastructure.models.base import (
    EDITORIAL_STATUS_CHECK,
    PERIOD_END_PRECISION_COLUMN,
    PERIOD_END_YEAR_COLUMN,
    PERIOD_START_PRECISION_COLUMN,
    PERIOD_START_YEAR_COLUMN,
    TEMPORAL_PRECISION_CHECK,
    MusicCatalogBase,
)
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_64, TEXT_1024


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
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(TEXT_64), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String(TEXT_64)), nullable=False)
    description: Mapped[str | None] = mapped_column(String(TEXT_1024))
    period_start_year: Mapped[int | None]
    period_start_precision: Mapped[str | None] = mapped_column(String(TEXT_32))
    period_end_year: Mapped[int | None]
    period_end_precision: Mapped[str | None] = mapped_column(String(TEXT_32))


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
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    period_start_year: Mapped[int | None]
    period_start_precision: Mapped[str | None] = mapped_column(String(TEXT_32))
    period_end_year: Mapped[int | None]
    period_end_precision: Mapped[str | None] = mapped_column(String(TEXT_32))
    roles_or_instruments: Mapped[list[str]] = mapped_column(ARRAY(String(TEXT_64)), nullable=False)
    provenance: Mapped[str | None] = mapped_column(String(TEXT_1024))


Index("ix_group_memberships_group_id", GroupMembershipRecord.group_id)
Index("ix_group_memberships_person_id", GroupMembershipRecord.person_id)
