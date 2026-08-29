"""Session lifecycle: create, sign players up, generate tables, close.

Errors:
    ValueError            invalid input (e.g. too few participants)
    SessionStateError     the operation is not allowed in the session's current
                          state (closed, tables already generated, ...)
    LookupError           a referenced player does not exist
"""

from __future__ import annotations

import datetime as dt
import random

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.domain.seating import MIN_PLAYERS, generate_rounds
from app.models import (
    GameTable,
    Participant,
    Player,
    Round,
    Seat,
    Session,
    SessionKind,
    SessionStatus,
)

_SEED_BITS = 31


class SessionStateError(ValueError):
    """Raised when an operation does not fit the session's current state."""


def create_session(db: DbSession, n_rounds: int, date: dt.date | None = None) -> Session:
    """Create an open session with no participants, closing any open one first.

    Raises:
        ValueError: if ``n_rounds < 1``.
    """
    if n_rounds < 1:
        raise ValueError(f"n_rounds must be >= 1, got {n_rounds}")
    current = get_current_session(db)
    if current is not None:
        current.status = SessionStatus.CLOSED
    session = Session(
        date=date or dt.date.today(),
        kind=SessionKind.FREE,
        status=SessionStatus.OPEN,
        n_rounds=n_rounds,
        seed=None,
    )
    db.add(session)
    db.commit()
    return session


def get_current_session(db: DbSession) -> Session | None:
    """The open session, or ``None``."""
    return db.scalar(select(Session).where(Session.status == SessionStatus.OPEN))


def get_session(db: DbSession, session_id: int) -> Session | None:
    """Load a session with its full tree, or ``None`` if missing."""
    return db.get(Session, session_id)


def list_sessions(db: DbSession) -> list[Session]:
    """All sessions, most recent first."""
    return list(db.scalars(select(Session).order_by(Session.date.desc(), Session.id.desc())))


def add_participant(db: DbSession, session: Session, player_id: int) -> Participant:
    """Sign a player up for an open session whose tables are not generated yet.

    Raises:
        SessionStateError: session closed, tables already generated, or the
            player is already signed up.
        LookupError: unknown ``player_id``.
    """
    _require_editable(session)
    player = db.get(Player, player_id)
    if player is None:
        raise LookupError(f"Unknown player id: {player_id}")
    if any(p.player_id == player_id for p in session.participants):
        raise SessionStateError(f"Player {player.name!r} is already signed up")
    participant = Participant(player=player)
    session.participants.append(participant)
    db.commit()
    return participant


def remove_participant(db: DbSession, session: Session, player_id: int) -> bool:
    """Remove a player from an open, not-yet-generated session.

    Returns ``False`` if the player was not signed up.

    Raises:
        SessionStateError: session closed or tables already generated.
    """
    _require_editable(session)
    for participant in session.participants:
        if participant.player_id == player_id:
            session.participants.remove(participant)
            db.commit()
            return True
    return False


def generate_tables(db: DbSession, session: Session, seed: int | None = None) -> Session:
    """Generate the seating for all rounds from the current participants.

    Args:
        seed: seating seed; drawn at random and stored when omitted.

    Raises:
        SessionStateError: session closed or tables already generated.
        ValueError: fewer than ``MIN_PLAYERS`` participants.
    """
    _require_editable(session)
    players = [p.player for p in session.participants]
    if len(players) < MIN_PLAYERS:
        raise ValueError(
            f"At least {MIN_PLAYERS} participants are required, got {len(players)}"
        )
    if seed is None:
        seed = random.getrandbits(_SEED_BITS)
    by_name = {p.name: p for p in players}
    schedule = generate_rounds([p.name for p in players], session.n_rounds, seed=seed)

    session.seed = seed
    for round_number, tables in enumerate(schedule, start=1):
        round_ = Round(number=round_number)
        for table_number, names in enumerate(tables, start=1):
            table = GameTable(number=table_number)
            table.seats = [
                Seat(player=by_name[name], position=position)
                for position, name in enumerate(names, start=1)
            ]
            round_.tables.append(table)
        session.rounds.append(round_)
    db.commit()
    return session


def close_session(db: DbSession, session: Session) -> Session:
    """Mark a session as closed.

    Raises:
        SessionStateError: already closed.
    """
    if session.status is SessionStatus.CLOSED:
        raise SessionStateError("Session is already closed")
    session.status = SessionStatus.CLOSED
    db.commit()
    return session


def delete_session(db: DbSession, session_id: int) -> bool:
    """Delete a session with its participants and seating; ``False`` if missing."""
    session = db.get(Session, session_id)
    if session is None:
        return False
    db.delete(session)
    db.commit()
    return True


def _require_editable(session: Session) -> None:
    if session.status is SessionStatus.CLOSED:
        raise SessionStateError("Session is closed")
    if session.tables_generated:
        raise SessionStateError("Tables are already generated; start a new session instead")
