from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.discovery.application.dto import GenreOverviewResponse, GenreRelationsResponse


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
