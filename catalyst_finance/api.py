"""FastAPI application boundary for Catalyst Finance."""

from __future__ import annotations

from typing import Any, cast

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from .engine import evaluate_payload
from .models import validation_issues
from .registry import get_model, list_models
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

    @application.get("/api/v1/models", tags=["models"])
    def models() -> dict[str, list[dict[str, Any]]]:
        return {"models": list_models()}

    @application.get("/api/v1/models/{model_id}", tags=["models"])
    def model(model_id: str) -> dict[str, Any]:
        record = get_model(model_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Unknown finance model")
        return record

    @application.post("/api/v1/evaluate", tags=["evaluation"])
    def evaluate_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                evaluate_payload(payload).model_dump(mode="json"),
            )
        except (ValidationError, ValueError) as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "invalid_finance_scenario",
                    "issues": validation_issues(exc),
                },
            ) from exc

    return application


app = create_app()
