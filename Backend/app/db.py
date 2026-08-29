"""Engine and session factory for the local SQLite database."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base

DEFAULT_DB_PATH = Path("data") / "serate.db"


def make_engine(db_path: Path | None = DEFAULT_DB_PATH) -> Engine:
    """Create a SQLite engine.

    Args:
        db_path: path of the database file, created on first use together with
            its parent directory. ``None`` gives an in-memory database (tests).
    """
    if db_path is None:
        url = "sqlite://"
    else:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{db_path}"
    engine = create_engine(url)

    # SQLite ignores foreign keys unless asked to on every connection.
    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def init_db(engine: Engine) -> None:
    """Create all tables that do not exist yet."""
    Base.metadata.create_all(engine)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Build a session factory bound to ``engine``."""
    return sessionmaker(bind=engine, expire_on_commit=False)