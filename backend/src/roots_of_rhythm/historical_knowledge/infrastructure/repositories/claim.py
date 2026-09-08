from typing import TYPE_CHECKING

from psycopg import errors as psycopg_errors
from sqlalchemy import delete, or_, select
from sqlalchemy.exc import IntegrityError

from roots_of_rhythm.historical_knowledge.application.errors import UniqueConstraintViolation
from roots_of_rhythm.historical_knowledge.infrastructure.mapping import (
    claim_from_records,
    evidence_records_from_claim,
    record_from_claim,
    update_claim_record,
)
from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    CLAIM_ENDPOINTS_UNIQUE_INDEX,
    ClaimEvidenceReferenceRecord,
    GenreRelationClaimRecord,
)
from roots_of_rhythm.infrastructure.database import apply_write_lock

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from roots_of_rhythm.historical_knowledge.domain import GenreRelationClaim


class SqlAlchemyClaimRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, claim: GenreRelationClaim) -> None:
        self._session.add(record_from_claim(claim))
        self._session.add_all(evidence_records_from_claim(claim))
        await self._flush_unique_constraint()

    async def get(self, claim_id: UUID, *, for_update: bool = False) -> GenreRelationClaim | None:
        record = await self._get_claim_record(claim_id, for_update=for_update)
        if record is None:
            return None
        evidence = await self._evidence_for([claim_id])
        return claim_from_records(record, evidence.get(claim_id, []))

    async def save(self, claim: GenreRelationClaim) -> None:
        record = await self._get_claim_record(claim.id, for_update=True)
        if record is None:
            raise LookupError(str(claim.id))
        update_claim_record(record, claim)
        await self._session.execute(
            delete(ClaimEvidenceReferenceRecord).where(ClaimEvidenceReferenceRecord.claim_id == claim.id)
        )
        self._session.add_all(evidence_records_from_claim(claim))
        await self._flush_unique_constraint()

    async def mark_deleted(self, claim_id: UUID) -> None:
        record = await self._get_claim_record(claim_id, for_update=True)
        if record is None:
            raise LookupError(str(claim_id))
        record.deleted = True
        await self._session.execute(
            delete(ClaimEvidenceReferenceRecord).where(ClaimEvidenceReferenceRecord.claim_id == claim_id)
        )

    async def list_by_genre(self, genre_id: UUID) -> list[GenreRelationClaim]:
        result = await self._session.execute(
            select(GenreRelationClaimRecord).where(
                or_(
                    GenreRelationClaimRecord.subject_genre_id == genre_id,
                    GenreRelationClaimRecord.target_genre_id == genre_id,
                ),
                GenreRelationClaimRecord.deleted.is_(False),
            )
        )
        records = list(result.scalars())
        evidence_by_claim = await self._evidence_for([record.id for record in records])
        return [claim_from_records(record, evidence_by_claim.get(record.id, [])) for record in records]

    async def _get_claim_record(self, claim_id: UUID, *, for_update: bool = False) -> GenreRelationClaimRecord | None:
        statement = select(GenreRelationClaimRecord).where(
            GenreRelationClaimRecord.id == claim_id,
            GenreRelationClaimRecord.deleted.is_(False),
        )
        result = await self._session.execute(apply_write_lock(statement, for_update=for_update))
        return result.scalar_one_or_none()

    async def _evidence_for(self, claim_ids: list[UUID]) -> dict[UUID, list[ClaimEvidenceReferenceRecord]]:
        if not claim_ids:
            return {}
        result = await self._session.execute(
            select(ClaimEvidenceReferenceRecord).where(ClaimEvidenceReferenceRecord.claim_id.in_(claim_ids))
        )
        grouped: dict[UUID, list[ClaimEvidenceReferenceRecord]] = {claim_id: [] for claim_id in claim_ids}
        for record in result.scalars():
            grouped[record.claim_id].append(record)
        return grouped

    async def _flush_unique_constraint(self) -> None:
        try:
            await self._session.flush()
        except IntegrityError as error:
            if (
                isinstance(error.orig, psycopg_errors.UniqueViolation)
                and error.orig.diag.constraint_name == CLAIM_ENDPOINTS_UNIQUE_INDEX
            ):
                raise UniqueConstraintViolation(CLAIM_ENDPOINTS_UNIQUE_INDEX) from error
            raise
