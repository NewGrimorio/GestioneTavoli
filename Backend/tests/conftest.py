from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session as DbSession

from app.db import init_db, make_engine, make_session_factory


@pytest.fixture
def db() -> Iterator[DbSession]:
    """Fresh in-memory database for every test."""
    engine = make_engine(None)
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as db:
        yield db
    engine.dispose()
