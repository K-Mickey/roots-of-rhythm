import click
import uvicorn

from roots_of_rhythm.config import settings


@click.group()
def cli() -> None:
    """Run Roots of Rhythm backend components."""


@cli.command("api")
@click.option("--host", default=None, help="Address to bind the API server to.")
@click.option("--port", default=None, type=click.IntRange(1, 65535), help="Port for the API server.")
@click.option("--reload/--no-reload", default=None, help="Enable or disable Uvicorn reload.")
def run_api(host: str | None, port: int | None, reload: bool | None) -> None:
    """Run the Litestar HTTP API."""
    uvicorn.run(
        "roots_of_rhythm.entrypoints.api:create_app",
        factory=True,
        host=host if host is not None else settings.api_host,
        port=port if port is not None else settings.api_port,
        reload=reload if reload is not None else settings.api_reload,
    )
