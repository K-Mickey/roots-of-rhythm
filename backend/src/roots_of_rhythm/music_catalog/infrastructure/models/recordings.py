from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from roots_of_rhythm.infrastructure.service_columns import ServiceColumnsMixin
from roots_of_rhythm.music_catalog.infrastructure.models.base import (
    BILLING_ROLE_CHECK,
    EDITORIAL_STATUS_CHECK,
    PERIOD_END_PRECISION_COLUMN,
    PERIOD_END_YEAR_COLUMN,
    PERIOD_START_PRECISION_COLUMN,
    PERIOD_START_YEAR_COLUMN,
    RECORDING_CONTRIBUTION_KIND_CHECK,
    RECORDING_CREDIT_TARGET_KIND_CHECK,
    RECORDING_WORK_USAGE_KIND_CHECK,
    RECORDING_WORK_USAGE_UNIQUE_CONSTRAINT,
    TEMPORAL_PRECISION_CHECK,
    MusicCatalogBase,
)
from roots_of_rhythm.text_lengths import TEXT_16, TEXT_32, TEXT_64, TEXT_1024


class RecordingRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "recordings"
    __table_args__ = (
        CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_recordings_editorial_status"),
        CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_START_YEAR_COLUMN,
                precision_column=PERIOD_START_PRECISION_COLUMN,
            ),
            name="ck_recordings_period_start",
        ),
        CheckConstraint(
            TEMPORAL_PRECISION_CHECK.format(
                year_column=PERIOD_END_YEAR_COLUMN,
                precision_column=PERIOD_END_PRECISION_COLUMN,
            ),
            name="ck_recordings_period_end",
        ),
        CheckConstraint(
            "period_start_year IS NULL OR period_end_year IS NULL OR period_start_year <= period_end_year",
            name="ck_recordings_period_order",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(TEXT_64), nullable=False)
    period_start_year: Mapped[int | None]
    period_start_precision: Mapped[str | None] = mapped_column(String(TEXT_32))
    period_end_year: Mapped[int | None]
    period_end_precision: Mapped[str | None] = mapped_column(String(TEXT_32))
    description: Mapped[str | None] = mapped_column(String(TEXT_1024))
    isrc: Mapped[str | None] = mapped_column(String(TEXT_16))
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)


Index("ix_recordings_editorial_status", RecordingRecord.editorial_status)


class RecordingCreditRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "recording_credits"
    __table_args__ = (
        CheckConstraint(RECORDING_CREDIT_TARGET_KIND_CHECK, name="ck_recording_credits_target_kind"),
        CheckConstraint(BILLING_ROLE_CHECK, name="ck_recording_credits_billing_role"),
        CheckConstraint(RECORDING_CONTRIBUTION_KIND_CHECK, name="ck_recording_credits_contribution_kind"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    recording_id: Mapped[UUID] = mapped_column(ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False)
    target_kind: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    target_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    billing_role: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    contribution_kind: Mapped[str | None] = mapped_column(String(TEXT_32))
    instrument: Mapped[str | None] = mapped_column(String(TEXT_64))
    credited_as: Mapped[str | None] = mapped_column(String(TEXT_64))


Index("ix_recording_credits_recording_id", RecordingCreditRecord.recording_id)
Index("ix_recording_credits_target", RecordingCreditRecord.target_kind, RecordingCreditRecord.target_id)


class RecordingWorkUsageRecord(ServiceColumnsMixin, MusicCatalogBase):
    __tablename__ = "recording_work_usages"
    __table_args__ = (
        CheckConstraint(RECORDING_WORK_USAGE_KIND_CHECK, name="ck_recording_work_usages_usage_kind"),
        CheckConstraint("position IS NULL OR position > 0", name="ck_recording_work_usages_position"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    recording_id: Mapped[UUID] = mapped_column(ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False)
    work_id: Mapped[UUID] = mapped_column(ForeignKey("musical_works.id", ondelete="RESTRICT"), nullable=False)
    usage_kind: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)
    position: Mapped[int | None]


Index(
    RECORDING_WORK_USAGE_UNIQUE_CONSTRAINT,
    RecordingWorkUsageRecord.recording_id,
    RecordingWorkUsageRecord.work_id,
    RecordingWorkUsageRecord.usage_kind,
    unique=True,
    postgresql_where=RecordingWorkUsageRecord.deleted.is_(False),
)
Index("ix_recording_work_usages_recording_id", RecordingWorkUsageRecord.recording_id)
Index("ix_recording_work_usages_work_id", RecordingWorkUsageRecord.work_id)
