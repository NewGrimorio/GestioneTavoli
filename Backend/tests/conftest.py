from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session

from app.db import init_db, make_engine, make_session_factory


@pytest.fixture
def session() -> Iterator[Session]:
    """Fresh in-memory database for every test."""
    engine = make_engine(None)
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as session:
        yield session
    engine.dispose()
