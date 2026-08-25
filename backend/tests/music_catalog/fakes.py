from typing import TYPE_CHECKING, Self

from roots_of_rhythm.music_catalog.domain import EditorialStatus

if TYPE_CHECKING:
    from collections.abc import Collection
    from types import TracebackType
    from uuid import UUID

    from roots_of_rhythm.music_catalog.application.ports import (
        ClassificationAssignmentRepository,
        GenreRepository,
        GroupMembershipRepository,
        GroupRepository,
    )
    from roots_of_rhythm.music_catalog.domain import ClassificationAssignment, Genre, Group, GroupMembership


class FakeClassificationAssignmentRepository:
    def __init__(self, assignments: dict[UUID, ClassificationAssignment]) -> None:
        self._assignments = assignments

    async def add(self, assignment: ClassificationAssignment) -> None:
        self._assignments[assignment.id] = assignment

    async def get(self, assignment_id: UUID, *, for_update: bool = False) -> ClassificationAssignment | None:
        return self._assignments.get(assignment_id)

    async def list_published_for_person(self, person_id: UUID) -> list[ClassificationAssignment]:
        return [
            assignment
            for assignment in self._assignments.values()
            if assignment.target_id == person_id and assignment.editorial_status is EditorialStatus.PUBLISHED
        ]

    async def save(self, assignment: ClassificationAssignment) -> None:
        if assignment.id not in self._assignments:
            raise LookupError(str(assignment.id))
        self._assignments[assignment.id] = assignment


class FakeGenreRepository:
    def __init__(self, genres: dict[UUID, Genre]) -> None:
        self._genres = genres

    async def add(self, genre: Genre) -> None:
        self._genres[genre.id] = genre

    async def get(self, genre_id: UUID, *, for_update: bool = False) -> Genre | None:
        return self._genres.get(genre_id)

    async def get_published(self, genre_id: UUID, *, for_update: bool = False) -> Genre | None:
        genre = self._genres.get(genre_id)
        return genre if genre is not None and genre.editorial_status is EditorialStatus.PUBLISHED else None

    async def get_published_by_ids(self, genre_ids: Collection[UUID]) -> dict[UUID, Genre]:
        return {
            genre_id: genre
            for genre_id in genre_ids
            if (genre := self._genres.get(genre_id)) is not None and genre.editorial_status is EditorialStatus.PUBLISHED
        }

    async def list_published(self) -> list[Genre]:
        return sorted(
            (genre for genre in self._genres.values() if genre.editorial_status is EditorialStatus.PUBLISHED),
            key=lambda genre: genre.content.canonical_name,
        )

    async def save(self, genre: Genre) -> None:
        self._genres[genre.id] = genre

    async def mark_deleted(self, genre_id: UUID) -> None:
        self._genres.pop(genre_id, None)

    async def published_among(self, genre_ids: Collection[UUID]) -> set[UUID]:
        return {
            genre_id
            for genre_id in genre_ids
            if (genre := self._genres.get(genre_id)) is not None and genre.editorial_status is EditorialStatus.PUBLISHED
        }

    async def canonical_name_exists(self, canonical_name: str, *, excluding: UUID | None = None) -> bool:
        return any(
            genre.id != excluding and genre.content.canonical_name.lower() == canonical_name.lower()
            for genre in self._genres.values()
        )


class FakeGroupRepository:
    def __init__(self, groups: dict[UUID, Group]) -> None:
        self._groups = groups

    async def add(self, group: Group) -> None:
        self._groups[group.id] = group

    async def get(self, group_id: UUID, *, for_update: bool = False) -> Group | None:
        return self._groups.get(group_id)

    async def get_published(self, group_id: UUID, *, for_update: bool = False) -> Group | None:
        group = self._groups.get(group_id)
        return group if group is not None and group.editorial_status is EditorialStatus.PUBLISHED else None

    async def list_published(self) -> list[Group]:
        return sorted(
            (group for group in self._groups.values() if group.editorial_status is EditorialStatus.PUBLISHED),
            key=lambda group: group.canonical_name,
        )

    async def save(self, group: Group) -> None:
        if group.id not in self._groups:
            raise LookupError(str(group.id))
        self._groups[group.id] = group

    async def mark_deleted(self, group_id: UUID) -> None:
        self._groups.pop(group_id, None)


class FakeGroupMembershipRepository:
    def __init__(self, memberships: dict[UUID, GroupMembership]) -> None:
        self._memberships = memberships

    async def add(self, membership: GroupMembership) -> None:
        self._memberships[membership.id] = membership

    async def get(self, membership_id: UUID, *, for_update: bool = False) -> GroupMembership | None:
        return self._memberships.get(membership_id)

    async def get_published(self, membership_id: UUID, *, for_update: bool = False) -> GroupMembership | None:
        membership = self._memberships.get(membership_id)
        if membership is None or membership.editorial_status is not EditorialStatus.PUBLISHED:
            return None
        return membership

    async def list_published_by_group(self, group_id: UUID) -> list[GroupMembership]:
        return sorted(
            (
                membership
                for membership in self._memberships.values()
                if membership.group_id == group_id and membership.editorial_status is EditorialStatus.PUBLISHED
            ),
            key=lambda membership: membership.id,
        )

    async def save(self, membership: GroupMembership) -> None:
        if membership.id not in self._memberships:
            raise LookupError(str(membership.id))
        self._memberships[membership.id] = membership

    async def mark_deleted(self, membership_id: UUID) -> None:
        self._memberships.pop(membership_id, None)


class FakeMusicCatalogUnitOfWork:
    def __init__(
        self,
        genres: dict[UUID, Genre],
        assignments: dict[UUID, ClassificationAssignment] | None = None,
        groups: dict[UUID, Group] | None = None,
        group_memberships: dict[UUID, GroupMembership] | None = None,
    ) -> None:
        self.genres: GenreRepository = FakeGenreRepository(genres)
        self.assignments: ClassificationAssignmentRepository = FakeClassificationAssignmentRepository(
            {} if assignments is None else assignments
        )
        self.groups: GroupRepository = FakeGroupRepository({} if groups is None else groups)
        self.group_memberships: GroupMembershipRepository = FakeGroupMembershipRepository(
            {} if group_memberships is None else group_memberships
        )
        self.commits = 0
        self.rollbacks = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.rollbacks += 1

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1
