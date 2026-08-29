"""FastAPI application factory.

Run locally with:  python -m uvicorn app.main:app --reload
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import DEFAULT_DB_PATH, init_db, make_engine, make_session_factory
from app.routers import evenings_router, players_router

# Vite dev server origins; irrelevant once the frontend is served by the backend itself.
DEV_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def create_app(db_path: Path | None = DEFAULT_DB_PATH) -> FastAPI:
    """Build the app bound to the SQLite file at ``db_path`` (``None`` = in-memory)."""
    engine = make_engine(db_path)
    init_db(engine)

    app = FastAPI(title="Gestione Tavoli", version="0.1.0")
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=DEV_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(players_router.router, prefix="/api")
    app.include_router(evenings_router.router, prefix="/api")

    @app.get("/api/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
