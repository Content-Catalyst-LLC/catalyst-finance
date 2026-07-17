"""FastAPI application boundary for Catalyst Finance."""

from __future__ import annotations

from fastapi import FastAPI

from .version import __version__


def create_app() -> FastAPI:
    application = FastAPI(
        title="Catalyst Finance API",
        version=__version__,
        docs_url="/api/docs",
        redoc_url=None,
    )

    @application.get("/healthz", tags=["system"])
    def healthz() -> dict[str, bool]:
        return {"ok": True}

    @application.get("/api/v1/version", tags=["system"])
    def version() -> dict[str, str]:
        return {
            "name": "Catalyst Finance",
            "version": __version__,
            "status": "ok",
        }

    return application


app = create_app()
