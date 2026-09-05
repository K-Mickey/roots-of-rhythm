from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.queries.song_list import SongListQuery
from roots_of_rhythm.music_catalog.domain import EditorialStatus, MusicalWork, WorkContent
from tests.discovery.readers_stubs import StubSongListReader


def _work(title: str, status: EditorialStatus) -> MusicalWork:
    return MusicalWork.create(
        uuid7(),
        WorkContent.create(title, provenance="Editorial review."),
        editorial_status=status,
    )


@pytest.mark.asyncio
async def test_song_list_query_maps_input_order() -> None:
    sixteen = _work("Sixteen Tons", EditorialStatus.PUBLISHED)
    ornithology = _work("Ornithology", EditorialStatus.PUBLISHED)
    query = SongListQuery(StubSongListReader(works=(sixteen, ornithology)))

    response = await query.list()

    assert [(item.id, item.name) for item in response.items] == [
        (str(sixteen.id), "Sixteen Tons"),
        (str(ornithology.id), "Ornithology"),
    ]


@pytest.mark.asyncio
async def test_song_list_query_empty_is_success() -> None:
    query = SongListQuery(StubSongListReader(works=()))

    response = await query.list()

    assert response.items == []
