import msgspec
from decouple import config  # type: ignore[import-untyped]  # python-decouple does not publish type metadata


class Settings(msgspec.Struct, frozen=True):
    database_url: str = config(
        "DATABASE_URL",
        default="postgresql+psycopg://roots:roots@127.0.0.1:5432/roots_of_rhythm",
    )
    api_host: str = config("API_HOST", default="127.0.0.1")
    api_port: int = config("API_PORT", default=8000, cast=int)
    api_reload: bool = config("API_RELOAD", default=False, cast=bool)


settings = Settings()
