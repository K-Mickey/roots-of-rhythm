from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import MusicalWork, WorkCredit, WorkRelation


class FakeMusicalWorkRepository:
    def __init__(self, works: dict[UUID, MusicalWork]) -> None:
        self._works = works
        self.locked_ids: list[UUID] = []
        self.batch_calls: list[tuple[UUID, ...]] = []

    async def add(self, work: MusicalWork) -> None:
        self._works[work.id] = work

    async def get(self, work_id: UUID, *, for_update: bool = False) -> MusicalWork | None:
        return self._works.get(work_id)

    async def get_published(self, work_id: UUID, *, for_update: bool = False) -> MusicalWork | None:
        if for_update:
            self.locked_ids.append(work_id)
        work = self._works.get(work_id)
        return work if work is not None and work.is_published else None

    async def get_published_by_ids(
        self, work_ids: Collection[UUID], *, for_update: bool = False
    ) -> dict[UUID, MusicalWork]:
        ids = sorted(set(work_ids))
        self.batch_calls.append(tuple(ids))
        if for_update:
            self.locked_ids.extend(ids)
        return {
            work_id: work for work_id in ids if (work := self._works.get(work_id)) is not None and work.is_published
        }

    async def list_published(self) -> list[MusicalWork]:
        return sorted(
            (work for work in self._works.values() if work.is_published),
            key=lambda work: work.canonical_title,
        )

    async def save(self, work: MusicalWork) -> None:
        if work.id not in self._works:
            raise LookupError(str(work.id))
        self._works[work.id] = work

    async def mark_deleted(self, work_id: UUID) -> None:
        self._works.pop(work_id, None)


class FakeWorkCreditRepository:
    def __init__(self, work_credits: dict[UUID, WorkCredit]) -> None:
        self._credits = work_credits

    async def add(self, credit: WorkCredit) -> None:
        self._credits[credit.id] = credit

    async def get(self, credit_id: UUID, *, for_update: bool = False) -> WorkCredit | None:
        return self._credits.get(credit_id)

    async def get_published(self, credit_id: UUID, *, for_update: bool = False) -> WorkCredit | None:
        credit = self._credits.get(credit_id)
        return credit if credit is not None and credit.is_published else None

    async def list_published_for_work(self, work_id: UUID) -> list[WorkCredit]:
        return sorted(
            (credit for credit in self._credits.values() if credit.work_id == work_id and credit.is_published),
            key=lambda credit: (credit.role.value, credit.id),
        )

    async def save(self, credit: WorkCredit) -> None:
        if credit.id not in self._credits:
            raise LookupError(str(credit.id))
        self._credits[credit.id] = credit

    async def mark_deleted(self, credit_id: UUID) -> None:
        self._credits.pop(credit_id, None)


class FakeWorkRelationRepository:
    def __init__(self, relations: dict[UUID, WorkRelation]) -> None:
        self._relations = relations

    async def add(self, relation: WorkRelation) -> None:
        self._relations[relation.id] = relation

    async def get(self, relation_id: UUID, *, for_update: bool = False) -> WorkRelation | None:
        return self._relations.get(relation_id)

    async def get_published(self, relation_id: UUID, *, for_update: bool = False) -> WorkRelation | None:
        relation = self._relations.get(relation_id)
        if relation is None or not relation.is_published:
            return None
        return relation

    async def list_published_for_work(self, work_id: UUID) -> list[WorkRelation]:
        return sorted(
            (
                relation
                for relation in self._relations.values()
                if relation.is_published and (relation.source_work_id == work_id or relation.target_work_id == work_id)
            ),
            key=lambda relation: (relation.relation_type.value, relation.id),
        )

    async def save(self, relation: WorkRelation) -> None:
        if relation.id not in self._relations:
            raise LookupError(str(relation.id))
        self._relations[relation.id] = relation

    async def mark_deleted(self, relation_id: UUID) -> None:
        self._relations.pop(relation_id, None)
