from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from roots_of_rhythm.historical_knowledge.infrastructure.models.base import (
    EDITORIAL_STATUS_CHECK,
    HistoricalKnowledgeBase,
)
from roots_of_rhythm.infrastructure.service_columns import ServiceColumnsMixin
from roots_of_rhythm.text_lengths import TEXT_32, TEXT_64, TEXT_1024

LISTENING_GUIDE_ACTIVE_RECORDING_INDEX = "uq_listening_guides_active_recording"
LISTENING_OBSERVATION_ACTIVE_POSITION_INDEX = "uq_listening_observations_active_position"
LISTENING_GUIDE_UNIQUE_CONSTRAINTS = frozenset(
    {LISTENING_GUIDE_ACTIVE_RECORDING_INDEX, LISTENING_OBSERVATION_ACTIVE_POSITION_INDEX}
)


class ListeningGuideRecord(ServiceColumnsMixin, HistoricalKnowledgeBase):
    __tablename__ = "listening_guides"
    __table_args__ = (CheckConstraint(EDITORIAL_STATUS_CHECK, name="ck_listening_guides_editorial_status"),)

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    recording_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    editorial_status: Mapped[str] = mapped_column(String(TEXT_32), nullable=False)


Index(
    LISTENING_GUIDE_ACTIVE_RECORDING_INDEX,
    ListeningGuideRecord.recording_id,
    unique=True,
    postgresql_where=ListeningGuideRecord.deleted.is_(False),
)


class ListeningObservationRecord(ServiceColumnsMixin, HistoricalKnowledgeBase):
    __tablename__ = "listening_observations"
    __table_args__ = (
        CheckConstraint("position > 0", name="ck_listening_observations_position"),
        CheckConstraint(
            "(start_seconds IS NULL AND end_seconds IS NULL) OR (start_seconds >= 0 AND end_seconds > start_seconds)",
            name="ck_listening_observations_range",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    guide_id: Mapped[UUID] = mapped_column(ForeignKey("listening_guides.id", ondelete="CASCADE"), nullable=False)
    feature: Mapped[str] = mapped_column(String(TEXT_64), nullable=False)
    explanation: Mapped[str] = mapped_column(String(TEXT_1024), nullable=False)
    context: Mapped[str | None] = mapped_column(String(TEXT_1024))
    author_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    authored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    start_seconds: Mapped[int | None]
    end_seconds: Mapped[int | None]
    position: Mapped[int] = mapped_column(nullable=False)


Index("ix_listening_observations_guide_id", ListeningObservationRecord.guide_id)
Index(
    LISTENING_OBSERVATION_ACTIVE_POSITION_INDEX,
    ListeningObservationRecord.guide_id,
    ListeningObservationRecord.position,
    unique=True,
    postgresql_where=ListeningObservationRecord.deleted.is_(False),
)
