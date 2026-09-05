from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import (
        ClassificationAssignment,
        Genre,
        Group,
        GroupMembership,
    )


@dataclass(frozen=True, slots=True)
class GroupOverviewData:
    group: Group | None
    assignments: tuple[ClassificationAssignment, ...]
    genres: dict[UUID, Genre]
    memberships: tuple[GroupMembership, ...]


class GroupReader(Protocol):
    async def list_published(self) -> tuple[Group, ...]: ...

    async def get_published_by_ids(self, group_ids: Collection[UUID]) -> dict[UUID, Group]: ...

    async def get_group_overview(self, group_id: UUID) -> GroupOverviewData: ...
