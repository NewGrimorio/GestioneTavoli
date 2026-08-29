"""Session endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session as DbSession

from app.models import Session
from app.routers.deps import get_db
from app.schemas import (
    GenerateTables,
    ParticipantAdd,
    PlayerRead,
    RoundRead,
    SessionCreate,
    SessionRead,
    SessionSummary,
    TableRead,
)
from app.services import sessions_service
from app.services.sessions_service import SessionStateError

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _summary(session: Session) -> SessionSummary:
    return SessionSummary(
        id=session.id,
        date=session.date,
        kind=session.kind,
        status=session.status,
        n_rounds=session.n_rounds,
        seed=session.seed,
        n_participants=len(session.participants),
        tables_generated=session.tables_generated,
    )


def _read(session: Session) -> SessionRead:
    return SessionRead(
        **_summary(session).model_dump(),
        participants=sorted(
            (PlayerRead.model_validate(p.player) for p in session.participants),
            key=lambda p: p.name.casefold(),
        ),
        rounds=[
            RoundRead(
                number=round_.number,
                tables=[
                    TableRead(
                        number=table.number,
                        players=[PlayerRead.model_validate(seat.player) for seat in table.seats],
                    )
                    for table in round_.tables
                ],
            )
            for round_ in session.rounds
        ],
    )


def _load(db: DbSession, session_id: int) -> Session:
    session = sessions_service.get_session(db, session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return session


@router.get("", response_model=list[SessionSummary])
def list_sessions(db: DbSession = Depends(get_db)) -> list[SessionSummary]:
    return [_summary(s) for s in sessions_service.list_sessions(db)]


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(body: SessionCreate, db: DbSession = Depends(get_db)) -> SessionRead:
    return _read(sessions_service.create_session(db, body.n_rounds, date=body.date))


# Declared before "/{session_id}" so that "current" is not parsed as an id.
@router.get("/current", response_model=SessionRead)
def get_current_session(db: DbSession = Depends(get_db)) -> SessionRead:
    session = sessions_service.get_current_session(db)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No open session")
    return _read(session)


@router.get("/{session_id}", response_model=SessionRead)
def get_session(session_id: int, db: DbSession = Depends(get_db)) -> SessionRead:
    return _read(_load(db, session_id))


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, db: DbSession = Depends(get_db)) -> Response:
    if not sessions_service.delete_session(db, session_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{session_id}/participants", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def add_participant(
    session_id: int, body: ParticipantAdd, db: DbSession = Depends(get_db)
) -> SessionRead:
    session = _load(db, session_id)
    try:
        sessions_service.add_participant(db, session, body.player_id)
    except SessionStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return _read(session)


@router.delete("/{session_id}/participants/{player_id}", response_model=SessionRead)
def remove_participant(
    session_id: int, player_id: int, db: DbSession = Depends(get_db)
) -> SessionRead:
    session = _load(db, session_id)
    try:
        removed = sessions_service.remove_participant(db, session, player_id)
    except SessionStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    if not removed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player is not signed up")
    return _read(session)


@router.post("/{session_id}/generate", response_model=SessionRead)
def generate_tables(
    session_id: int, body: GenerateTables | None = None, db: DbSession = Depends(get_db)
) -> SessionRead:
    session = _load(db, session_id)
    try:
        sessions_service.generate_tables(db, session, seed=body.seed if body else None)
    except SessionStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return _read(session)


@router.post("/{session_id}/close", response_model=SessionRead)
def close_session(session_id: int, db: DbSession = Depends(get_db)) -> SessionRead:
    session = _load(db, session_id)
    try:
        sessions_service.close_session(db, session)
    except SessionStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return _read(session)
