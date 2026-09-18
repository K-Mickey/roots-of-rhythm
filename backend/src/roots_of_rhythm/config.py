import msgspec
from decouple import config  # type: ignore[import-untyped]  # python-decouple does not publish type metadata


class Settings(msgspec.Struct, frozen=True):
    database_url: str = config(
        "DATABASE_URL",
        default="postgresql+asyncpg://roots:roots@127.0.0.1:5432/roots_of_rhythm",
    )
    api_host: str = config("API_HOST", default="127.0.0.1")
    api_port: int = config("API_PORT", default=8000, cast=int)
    api_reload: bool = config("API_RELOAD", default=False, cast=bool)
    develop: bool = config("DEVELOP", default=False, cast=bool)


class PGSettings(msgspec.Struct, frozen=True, kw_only=True):
    database: str = config("PG_DATABASE", default="roots_of_rhythm")
    host: str = config("PG_HOST", default="127.0.0.1")
    port: int = config("PG_PORT", default=5432, cast=int)
    username: str | None = config("PG_USERNAME", default="roots")
    password: str | None = config("PG_PASSWORD", default="roots")


settings = Settings()
pg_settings = PGSettings()
