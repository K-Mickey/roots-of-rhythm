from typing import TYPE_CHECKING

from psycopg import errors as psycopg_errors
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from roots_of_rhythm.historical_knowledge.application.errors import UniqueConstraintViolation
from roots_of_rhythm.historical_knowledge.domain import EditorialStatus, EvidenceStatus
from roots_of_rhythm.historical_knowledge.infrastructure.mapping import (
    evidence_records_from_recording_origin_claim,
    record_from_recording_origin_claim,
    recording_origin_claim_from_records,
    update_recording_origin_claim_record,
)
from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    RECORDING_ORIGIN_ENDPOINTS_UNIQUE_INDEX,
    RecordingOriginClaimEvidenceReferenceRecord,
    RecordingOriginClaimRecord,
)
from roots_of_rhythm.infrastructure.database import apply_write_lock

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from roots_of_rhythm.historical_knowledge.domain import RecordingOriginClaim


class SqlAlchemyRecordingOriginClaimRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, claim: RecordingOriginClaim) -> None:
        self._session.add(record_from_recording_origin_claim(claim))
        self._session.add_all(evidence_records_from_recording_origin_claim(claim))
        try:
            await self._session.flush()
        except IntegrityError as error:
            if (
                isinstance(error.orig, psycopg_errors.UniqueViolation)
                and error.orig.diag.constraint_name == RECORDING_ORIGIN_ENDPOINTS_UNIQUE_INDEX
            ):
                raise UniqueConstraintViolation(RECORDING_ORIGIN_ENDPOINTS_UNIQUE_INDEX) from error
            raise

    async def get(self, claim_id: UUID, *, for_update: bool = False) -> RecordingOriginClaim | None:
        record = await self._get_claim_record(claim_id, for_update=for_update)
        if record is None:
            return None
        evidence = await self._evidence_for([claim_id])
        return recording_origin_claim_from_records(record, evidence.get(claim_id, []))

    async def save(self, claim: RecordingOriginClaim) -> None:
        record = await self._get_claim_record(claim.id, for_update=True)
        if record is None:
            raise LookupError(str(claim.id))
        update_recording_origin_claim_record(record, claim)
        await self._session.execute(
            delete(RecordingOriginClaimEvidenceReferenceRecord).where(
                RecordingOriginClaimEvidenceReferenceRecord.claim_id == claim.id
            )
        )
        self._session.add_all(evidence_records_from_recording_origin_claim(claim))

    async def mark_deleted(self, claim_id: UUID) -> None:
        record = await self._get_claim_record(claim_id, for_update=True)
        if record is None:
            raise LookupError(str(claim_id))
        record.deleted = True
        await self._session.execute(
            delete(RecordingOriginClaimEvidenceReferenceRecord).where(
                RecordingOriginClaimEvidenceReferenceRecord.claim_id == claim_id
            )
        )

    async def list_supported_published_for_recordings(
        self,
        recording_ids: Collection[UUID],
    ) -> dict[UUID, list[RecordingOriginClaim]]:
        ids = list(recording_ids)
        if not ids:
            return {}
        statement = select(RecordingOriginClaimRecord).where(
            RecordingOriginClaimRecord.recording_id.in_(ids),
            RecordingOriginClaimRecord.editorial_status == EditorialStatus.PUBLISHED.value,
            RecordingOriginClaimRecord.evidence_status == EvidenceStatus.SUPPORTED.value,
            RecordingOriginClaimRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        records = list(result.scalars())
        evidence_by_claim = await self._evidence_for([record.id for record in records])
        grouped: dict[UUID, list[RecordingOriginClaim]] = {recording_id: [] for recording_id in ids}
        for record in records:
            claim = recording_origin_claim_from_records(record, evidence_by_claim.get(record.id, []))
            grouped[record.recording_id].append(claim)
        return grouped

    async def _get_claim_record(
        self,
        claim_id: UUID,
        *,
        for_update: bool = False,
    ) -> RecordingOriginClaimRecord | None:
        statement = select(RecordingOriginClaimRecord).where(
            RecordingOriginClaimRecord.id == claim_id,
            RecordingOriginClaimRecord.deleted.is_(False),
        )
        statement = apply_write_lock(statement, for_update=for_update)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def _evidence_for(
        self,
        claim_ids: list[UUID],
    ) -> dict[UUID, list[RecordingOriginClaimEvidenceReferenceRecord]]:
        if not claim_ids:
            return {}
        result = await self._session.execute(
            select(RecordingOriginClaimEvidenceReferenceRecord).where(
                RecordingOriginClaimEvidenceReferenceRecord.claim_id.in_(claim_ids)
            )
        )
        grouped: dict[UUID, list[RecordingOriginClaimEvidenceReferenceRecord]] = {
            claim_id: [] for claim_id in claim_ids
        }
        for record in result.scalars():
            grouped[record.claim_id].append(record)
        return grouped
