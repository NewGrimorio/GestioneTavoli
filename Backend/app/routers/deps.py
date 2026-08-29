"""FastAPI dependencies shared by the routers."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session as DbSession


def get_db(request: Request) -> Iterator[DbSession]:
    """Yield a database session bound to the app's engine, closed after the request."""
    factory = request.app.state.session_factory
    with factory() as db:
        yield db
