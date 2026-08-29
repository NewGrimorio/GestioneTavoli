"""FastAPI dependencies shared by the routers."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session


def get_session(request: Request) -> Iterator[Session]:
    """Yield a database session bound to the app's engine, closed after the request."""
    factory = request.app.state.session_factory
    with factory() as session:
        yield session