from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import GroupSummary
from roots_of_rhythm.discovery.application.dto.groups import GroupListResponse

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.public.group_reader import GroupReader


@runtime_checkable
class GroupListReader(Protocol):
    async def list(self) -> GroupListResponse: ...


class GroupListQuery:
    def __init__(self, groups: GroupReader) -> None:
        self._groups = groups

    async def list(self) -> GroupListResponse:
        groups = await self._groups.list_published()
        return GroupListResponse(
            items=[GroupSummary(id=str(group.id), name=group.canonical_name) for group in groups],
        )
