from typing import TYPE_CHECKING

from sqlalchemy import delete, or_, select, update

from roots_of_rhythm.historical_knowledge.domain import FragmentReviewStatus
from roots_of_rhythm.historical_knowledge.infrastructure.mapping import (
    claim_from_records,
    evidence_records_from_claim,
    fragment_from_record,
    record_from_claim,
    record_from_fragment,
    record_from_source,
    record_from_version,
    source_from_record,
    update_claim_record,
    update_fragment_record,
    version_from_record,
)
from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    ClaimEvidenceReferenceRecord,
    GenreRelationClaimRecord,
    SourceFragmentRecord,
    SourceRecord,
    SourceVersionRecord,
)

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from roots_of_rhythm.historical_knowledge.domain import (
        GenreRelationClaim,
        Source,
        SourceFragment,
        SourceVersion,
    )


class SqlAlchemyClaimRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, claim: GenreRelationClaim) -> None:
        self._session.add(record_from_claim(claim))
        self._session.add_all(evidence_records_from_claim(claim))

    async def get(self, claim_id: UUID) -> GenreRelationClaim | None:
        record = await self._get_claim_record(claim_id)
        if record is None:
            return None
        evidence = await self._evidence_for([claim_id])
        return claim_from_records(record, evidence.get(claim_id, []))

    async def save(self, claim: GenreRelationClaim) -> None:
        record = await self._get_claim_record(claim.id)
        if record is None:
            raise LookupError(str(claim.id))
        update_claim_record(record, claim)
        await self._session.execute(
            delete(ClaimEvidenceReferenceRecord).where(ClaimEvidenceReferenceRecord.claim_id == claim.id)
        )
        self._session.add_all(evidence_records_from_claim(claim))

    async def mark_deleted(self, claim_id: UUID) -> None:
        record = await self._get_claim_record(claim_id)
        if record is None:
            raise LookupError(str(claim_id))
        record.deleted = True
        await self._session.execute(
            delete(ClaimEvidenceReferenceRecord).where(ClaimEvidenceReferenceRecord.claim_id == claim_id)
        )

    async def list_by_genre(self, genre_id: UUID) -> list[GenreRelationClaim]:
        statement = select(GenreRelationClaimRecord).where(
            or_(
                GenreRelationClaimRecord.subject_genre_id == genre_id,
                GenreRelationClaimRecord.target_genre_id == genre_id,
            ),
            GenreRelationClaimRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        records = list(result.scalars())
        evidence_by_claim = await self._evidence_for([record.id for record in records])
        return [claim_from_records(record, evidence_by_claim.get(record.id, [])) for record in records]

    async def _get_claim_record(self, claim_id: UUID) -> GenreRelationClaimRecord | None:
        statement = select(GenreRelationClaimRecord).where(
            GenreRelationClaimRecord.id == claim_id,
            GenreRelationClaimRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
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


class SqlAlchemySourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_source(self, source: Source) -> None:
        self._session.add(record_from_source(source))

    async def add_version(self, version: SourceVersion) -> None:
        self._session.add(record_from_version(version))

    async def add_fragment(self, fragment: SourceFragment) -> None:
        self._session.add(record_from_fragment(fragment))

    async def get_source(self, source_id: UUID) -> Source | None:
        statement = select(SourceRecord).where(
            SourceRecord.id == source_id,
            SourceRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        return None if record is None else source_from_record(record)

    async def get_sources_by_ids(self, source_ids: Collection[UUID]) -> dict[UUID, Source]:
        ids = set(source_ids)
        if not ids:
            return {}
        statement = select(SourceRecord).where(
            SourceRecord.id.in_(ids),
            SourceRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        return {record.id: source_from_record(record) for record in result.scalars()}

    async def get_version(self, version_id: UUID) -> SourceVersion | None:
        statement = select(SourceVersionRecord).where(
            SourceVersionRecord.id == version_id,
            SourceVersionRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        return None if record is None else version_from_record(record)

    async def get_fragment(self, fragment_id: UUID) -> SourceFragment | None:
        statement = select(SourceFragmentRecord).where(
            SourceFragmentRecord.id == fragment_id,
            SourceFragmentRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        return None if record is None else fragment_from_record(record)

    async def save_fragment(self, fragment: SourceFragment) -> None:
        statement = select(SourceFragmentRecord).where(
            SourceFragmentRecord.id == fragment.id,
            SourceFragmentRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        if record is None:
            raise LookupError(str(fragment.id))
        update_fragment_record(record, fragment)

    async def reviewed_source_ids_for_fragments(self, fragment_ids: Collection[UUID]) -> dict[UUID, UUID]:
        ids = set(fragment_ids)
        if not ids:
            return {}
        statement = (
            select(SourceFragmentRecord.id, SourceVersionRecord.source_id)
            .join(
                SourceVersionRecord,
                SourceVersionRecord.id == SourceFragmentRecord.source_version_id,
            )
            .where(
                SourceFragmentRecord.id.in_(ids),
                SourceFragmentRecord.deleted.is_(False),
                SourceFragmentRecord.review_status == FragmentReviewStatus.REVIEWED.value,
                SourceVersionRecord.deleted.is_(False),
            )
        )
        result = await self._session.execute(statement)
        return dict(result.tuples().all())

    async def mark_source_deleted(self, source_id: UUID) -> None:
        statement = select(SourceRecord).where(
            SourceRecord.id == source_id,
            SourceRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        if record is None:
            raise LookupError(str(source_id))
        record.deleted = True
        version_ids = list(
            (
                await self._session.execute(
                    select(SourceVersionRecord.id).where(
                        SourceVersionRecord.source_id == source_id,
                        SourceVersionRecord.deleted.is_(False),
                    )
                )
            ).scalars()
        )
        if version_ids:
            await self._session.execute(
                update(SourceVersionRecord).where(SourceVersionRecord.id.in_(version_ids)).values(deleted=True)
            )
            await self._session.execute(
                update(SourceFragmentRecord)
                .where(
                    SourceFragmentRecord.source_version_id.in_(version_ids),
                    SourceFragmentRecord.deleted.is_(False),
                )
                .values(deleted=True)
            )

    async def mark_version_deleted(self, version_id: UUID) -> None:
        statement = select(SourceVersionRecord).where(
            SourceVersionRecord.id == version_id,
            SourceVersionRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        if record is None:
            raise LookupError(str(version_id))
        record.deleted = True
        await self._session.execute(
            update(SourceFragmentRecord)
            .where(
                SourceFragmentRecord.source_version_id == version_id,
                SourceFragmentRecord.deleted.is_(False),
            )
            .values(deleted=True)
        )

    async def mark_fragment_deleted(self, fragment_id: UUID) -> None:
        statement = select(SourceFragmentRecord).where(
            SourceFragmentRecord.id == fragment_id,
            SourceFragmentRecord.deleted.is_(False),
        )
        result = await self._session.execute(statement)
        record = result.scalar_one_or_none()
        if record is None:
            raise LookupError(str(fragment_id))
        record.deleted = True
