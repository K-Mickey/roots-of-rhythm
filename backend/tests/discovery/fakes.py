from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.discovery.application.dto import (
        GenreListResponse,
        GenreOverviewResponse,
        GenreRelationsResponse,
        GenreSourcesResponse,
        GroupListResponse,
        GroupOverviewResponse,
        PerformerListResponse,
        PerformerOverviewResponse,
    )


class StubGenreListReader:
    def __init__(self, result: GenreListResponse | Exception) -> None:
        self._result = result

    async def list(self) -> GenreListResponse:
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class StubGenreOverviewReader:
    def __init__(self, result: GenreOverviewResponse | Exception) -> None:
        self._result = result

    async def get(self, genre_id: UUID) -> GenreOverviewResponse:
        del genre_id
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class StubGenreRelationsReader:
    def __init__(self, result: GenreRelationsResponse | Exception) -> None:
        self._result = result

    async def get(self, genre_id: UUID) -> GenreRelationsResponse:
        del genre_id
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class StubGenreSourcesReader:
    def __init__(self, result: GenreSourcesResponse | Exception) -> None:
        self._result = result

    async def get(self, genre_id: UUID) -> GenreSourcesResponse:
        del genre_id
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class StubPerformerListReader:
    def __init__(self, result: PerformerListResponse | Exception) -> None:
        self._result = result

    async def list(self) -> PerformerListResponse:
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class StubPerformerOverviewReader:
    def __init__(self, result: PerformerOverviewResponse | Exception) -> None:
        self._result = result

    async def get(self, performer_id: UUID) -> PerformerOverviewResponse:
        del performer_id
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class StubGroupListReader:
    def __init__(self, result: GroupListResponse | Exception) -> None:
        self._result = result

    async def list(self) -> GroupListResponse:
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class StubGroupOverviewReader:
    def __init__(self, result: GroupOverviewResponse | Exception) -> None:
        self._result = result

    async def get(self, group_id: UUID) -> GroupOverviewResponse:
        del group_id
        if isinstance(self._result, Exception):
            raise self._result
        return self._result
