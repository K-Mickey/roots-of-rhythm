from roots_of_rhythm.discovery.presentation.genres import create_genres_router
from roots_of_rhythm.discovery.presentation.groups import create_groups_router
from roots_of_rhythm.discovery.presentation.performers import create_performers_router
from roots_of_rhythm.discovery.presentation.recordings import create_recordings_router
from roots_of_rhythm.discovery.presentation.songs import create_songs_router

__all__ = [
    "create_genres_router",
    "create_groups_router",
    "create_performers_router",
    "create_recordings_router",
    "create_songs_router",
]
