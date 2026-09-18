from litestar import Router

from roots_of_rhythm.discovery.presentation import (
    create_genres_router,
    create_groups_router,
    create_performers_router,
    create_recordings_router,
    create_songs_router,
)


def create_api_router() -> Router:
    return Router(
        path="/api/v1",
        route_handlers=[
            create_genres_router(),
            create_performers_router(),
            create_groups_router(),
            create_songs_router(),
            create_recordings_router(),
        ],
    )
