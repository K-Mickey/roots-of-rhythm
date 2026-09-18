from typing import TYPE_CHECKING

import msgspec
from sqlalchemy.ext.asyncio import async_sessionmaker

if TYPE_CHECKING:
    from typing import Final

    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

    from roots_of_rhythm.config import PGSettings

PG_RO_CHILD_INFO_KEY: Final = "pg_ro_child"
CHILD_CANCEL_GRACE_SECONDS: Final = 1.0


class PgConfig(msgspec.Struct, frozen=True, kw_only=True):
    database: str
    host: str = "127.0.0.1"
    port: int = 5432
    username: str | None = None
    password: str | None = None
    reconnect_timeout: int = 1
    pool_recycle: int = -1
    pool_min_size: int = 0
    pool_max_size: int = 5
    max_overflow: int = 10
    pool_timeout: float = 30.0
    pool_use_lifo: bool = False
    ro_pool_max_size: int = 5
    ro_max_overflow: int = 15
    query_cache_size: int = 500
    autoflush: bool = False
    autocommit: bool = False
    expire_on_commit: bool = False

    def __post_init__(self) -> None:
        if self.pool_min_size > self.pool_max_size:
            raise ValueError("pool_min_size must be <= pool_max_size")
        if self.ro_pool_max_size < 1:
            raise ValueError("ro_pool_max_size must be >= 1")
        if self.ro_max_overflow < 0:
            raise ValueError("ro_max_overflow must be >= 0")


def create_pg_config(settings: PGSettings) -> PgConfig:
    return PgConfig(
        database=settings.database,
        host=settings.host,
        port=settings.port,
        username=settings.username,
        password=settings.password,
    )


def build_session_makers(
    engine: AsyncEngine,
    ro_engine: AsyncEngine,
    config: PgConfig,
) -> tuple[async_sessionmaker[AsyncSession], async_sessionmaker[AsyncSession]]:
    rw = async_sessionmaker(
        bind=engine,
        autoflush=config.autoflush,
        expire_on_commit=config.expire_on_commit,
    )
    ro = async_sessionmaker(
        bind=ro_engine.execution_options(postgresql_readonly=True),
        autoflush=config.autoflush,
        expire_on_commit=config.expire_on_commit,
        info={PG_RO_CHILD_INFO_KEY: True},
    )
    return rw, ro
