from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.discovery.application.dto import GenreOverviewResponse


class StubGenreOverviewReader:
    def __init__(self, result: GenreOverviewResponse | Exception) -> None:
        self._result = result

    async def get(self, genre_id: UUID) -> GenreOverviewResponse:
        del genre_id
        if isinstance(self._result, Exception):
            raise self._result
        return self._result
