import datetime as dt

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.domain.seating import table_sizes
from app.models import Participant, Player, Seat, Session, SessionKind, SessionStatus
from app.services.players_service import create_player
from app.services.sessions_service import (
    SessionStateError,
    add_participant,
    close_session,
    create_session,
    delete_session,
    generate_tables,
    get_current_session,
    get_session,
    list_sessions,
    remove_participant,
)


def _register(db: DbSession, n: int) -> list[int]:
    return [create_player(db, f"P{i:02d}").id for i in range(n)]


def _session_with(db: DbSession, n_players: int, n_rounds: int = 3) -> Session:
    session = create_session(db, n_rounds)
    for player_id in _register(db, n_players):
        add_participant(db, session, player_id)
    return session


def _seating(session: Session) -> list[list[list[str]]]:
    return [
        [[seat.player.name for seat in table.seats] for table in round_.tables]
        for round_ in session.rounds
    ]


# --------------------------------------------------------------------------- #
# create / current / list
# --------------------------------------------------------------------------- #


def test_create_open_empty_session(db: DbSession) -> None:
    session = create_session(db, 3, date=dt.date(2026, 8, 29))
    assert session.id is not None
    assert session.status is SessionStatus.OPEN
    assert session.kind is SessionKind.FREE
    assert session.date == dt.date(2026, 8, 29)
    assert session.n_rounds == 3
    assert session.seed is None
    assert session.participants == []
    assert session.tables_generated is False
    assert get_current_session(db) is session


def test_defaults_to_today(db: DbSession) -> None:
    assert create_session(db, 1).date == dt.date.today()


def test_creating_closes_previous_open_session(db: DbSession) -> None:
    first = create_session(db, 2)
    second = create_session(db, 2)
    assert first.status is SessionStatus.CLOSED
    assert second.status is SessionStatus.OPEN
    assert get_current_session(db) is second


def test_no_current_session_when_all_closed(db: DbSession) -> None:
    session = create_session(db, 1)
    close_session(db, session)
    assert get_current_session(db) is None


@pytest.mark.parametrize("n_rounds", [0, -1])
def test_rejects_invalid_round_count(db: DbSession, n_rounds: int) -> None:
    with pytest.raises(ValueError):
        create_session(db, n_rounds)
    assert list_sessions(db) == []


def test_get_and_list_most_recent_first(db: DbSession) -> None:
    older = create_session(db, 1, date=dt.date(2026, 1, 10))
    newer = create_session(db, 1, date=dt.date(2026, 3, 5))
    assert get_session(db, older.id) is older
    assert get_session(db, 12345) is None
    assert [s.id for s in list_sessions(db)] == [newer.id, older.id]


# --------------------------------------------------------------------------- #
# participants
# --------------------------------------------------------------------------- #


def test_add_and_remove_participants(db: DbSession) -> None:
    session = create_session(db, 1)
    a, b = _register(db, 2)
    add_participant(db, session, a)
    add_participant(db, session, b)
    assert [p.player_id for p in session.participants] == [a, b]

    assert remove_participant(db, session, a) is True
    assert [p.player_id for p in session.participants] == [b]
    assert remove_participant(db, session, a) is False


def test_add_unknown_player(db: DbSession) -> None:
    session = create_session(db, 1)
    with pytest.raises(LookupError):
        add_participant(db, session, 999)


def test_add_same_player_twice(db: DbSession) -> None:
    session = create_session(db, 1)
    (player_id,) = _register(db, 1)
    add_participant(db, session, player_id)
    with pytest.raises(SessionStateError):
        add_participant(db, session, player_id)


def test_cannot_edit_participants_of_closed_session(db: DbSession) -> None:
    session = create_session(db, 1)
    (player_id,) = _register(db, 1)
    close_session(db, session)
    with pytest.raises(SessionStateError):
        add_participant(db, session, player_id)
    with pytest.raises(SessionStateError):
        remove_participant(db, session, player_id)


def test_cannot_edit_participants_after_generation(db: DbSession) -> None:
    """A latecomer is not allowed: the organizer starts a new session instead."""
    session = _session_with(db, 6)
    generate_tables(db, session, seed=1)
    (latecomer,) = [create_player(db, "Late").id]
    with pytest.raises(SessionStateError):
        add_participant(db, session, latecomer)
    with pytest.raises(SessionStateError):
        remove_participant(db, session, session.participants[0].player_id)


# --------------------------------------------------------------------------- #
# generate tables
# --------------------------------------------------------------------------- #


def test_generate_builds_full_tree(db: DbSession) -> None:
    session = _session_with(db, 22, n_rounds=3)
    generate_tables(db, session, seed=1)

    assert session.seed == 1
    assert session.tables_generated is True
    assert session.status is SessionStatus.OPEN
    assert [r.number for r in session.rounds] == [1, 2, 3]
    ids = sorted(p.player_id for p in session.participants)
    for round_ in session.rounds:
        assert [t.number for t in round_.tables] == [1, 2, 3, 4, 5, 6]
        assert [len(t.seats) for t in round_.tables] == table_sizes(22)
        assert sorted(seat.player_id for t in round_.tables for seat in t.seats) == ids


def test_generate_draws_and_stores_seed_when_omitted(db: DbSession) -> None:
    session = _session_with(db, 8, n_rounds=2)
    generate_tables(db, session)
    assert isinstance(session.seed, int)
    assert session.seed >= 0


def test_same_seed_replays_same_seating(db: DbSession) -> None:
    first = _session_with(db, 22)
    generate_tables(db, first, seed=42)
    second = create_session(db, 3)
    for participant in first.participants:
        add_participant(db, second, participant.player_id)
    generate_tables(db, second, seed=42)
    assert _seating(first) == _seating(second)


def test_generate_requires_six_participants(db: DbSession) -> None:
    session = _session_with(db, 5)
    with pytest.raises(ValueError, match="At least 6"):
        generate_tables(db, session, seed=1)
    assert session.tables_generated is False
    assert session.seed is None


def test_generate_twice_is_rejected(db: DbSession) -> None:
    session = _session_with(db, 6)
    generate_tables(db, session, seed=1)
    with pytest.raises(SessionStateError):
        generate_tables(db, session, seed=2)
    assert session.seed == 1


def test_generate_on_closed_session_is_rejected(db: DbSession) -> None:
    session = _session_with(db, 6)
    close_session(db, session)
    with pytest.raises(SessionStateError):
        generate_tables(db, session, seed=1)


# --------------------------------------------------------------------------- #
# close / delete
# --------------------------------------------------------------------------- #


def test_close_twice_is_rejected(db: DbSession) -> None:
    session = create_session(db, 1)
    close_session(db, session)
    with pytest.raises(SessionStateError):
        close_session(db, session)


def test_delete_removes_tree_but_keeps_players(db: DbSession) -> None:
    session = _session_with(db, 6, n_rounds=2)
    generate_tables(db, session, seed=1)
    assert delete_session(db, session.id) is True
    assert delete_session(db, session.id) is False
    assert db.scalar(select(Seat).limit(1)) is None
    assert db.scalar(select(Participant).limit(1)) is None
    assert len(db.scalars(select(Player)).all()) == 6


def test_closed_sessions_keep_their_history(db: DbSession) -> None:
    """Old sessions stay readable with the names of the players of that time."""
    old = _session_with(db, 6, n_rounds=1)
    generate_tables(db, old, seed=1)
    create_session(db, 1)  # closes ``old``
    reloaded = get_session(db, old.id)
    assert reloaded is not None
    assert reloaded.status is SessionStatus.CLOSED
    assert len(reloaded.participants) == 6
    assert _seating(reloaded) == _seating(old)
