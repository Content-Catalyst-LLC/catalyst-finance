"""ASGI compatibility entry point.

Run locally with:
    uvicorn app:app --reload
"""

from catalyst_finance.api import app, create_app

__all__ = ["app", "create_app"]
