import datetime as dt

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.seating import table_sizes
from app.models import Evening, EveningKind, Player, Seat
from app.services.evenings_service import create_free_evening, get_evening, list_evenings
from app.services.players_service import create_player


def _register(session: Session, n: int) -> list[int]:
    return [create_player(session, f"P{i:02d}").id for i in range(n)]


def _seating(evening: Evening) -> list[list[list[str]]]:
    return [
        [[seat.player.name for seat in table.seats] for table in round_.tables]
        for round_ in evening.rounds
    ]


def test_builds_full_tree(session: Session) -> None:
    ids = _register(session, 22)
    evening = create_free_evening(session, ids, n_rounds=3, seed=1)

    assert evening.id is not None
    assert evening.kind is EveningKind.FREE
    assert evening.n_rounds == 3
    assert evening.seed == 1
    assert [r.number for r in evening.rounds] == [1, 2, 3]
    for round_ in evening.rounds:
        assert [t.number for t in round_.tables] == [1, 2, 3, 4, 5, 6]
        assert [len(t.seats) for t in round_.tables] == table_sizes(22)
        seated = sorted(seat.player_id for t in round_.tables for seat in t.seats)
        assert seated == sorted(ids)


def test_seed_is_drawn_and_stored_when_omitted(session: Session) -> None:
    ids = _register(session, 8)
    evening = create_free_evening(session, ids, n_rounds=2)
    assert isinstance(evening.seed, int)
    assert evening.seed >= 0


def test_same_seed_replays_same_seating(session: Session) -> None:
    ids = _register(session, 22)
    first = create_free_evening(session, ids, n_rounds=3, seed=42)
    second = create_free_evening(session, ids, n_rounds=3, seed=42)
    assert _seating(first) == _seating(second)


def test_defaults_to_today_and_accepts_explicit_date(session: Session) -> None:
    ids = _register(session, 6)
    assert create_free_evening(session, ids, 1).date == dt.date.today()
    when = dt.date(2026, 8, 29)
    assert create_free_evening(session, ids, 1, date=when).date == when


def test_rejects_unknown_player(session: Session) -> None:
    ids = _register(session, 6)
    with pytest.raises(ValueError, match="Unknown player ids"):
        create_free_evening(session, ids + [999], 1)


def test_rejects_duplicate_player_ids(session: Session) -> None:
    ids = _register(session, 6)
    with pytest.raises(ValueError, match="unique"):
        create_free_evening(session, ids + [ids[0]], 1)


def test_rejects_invalid_rounds_and_leaves_nothing_behind(session: Session) -> None:
    ids = _register(session, 6)
    with pytest.raises(ValueError):
        create_free_evening(session, ids, 0)
    assert list_evenings(session) == []


def test_get_and_list(session: Session) -> None:
    ids = _register(session, 6)
    older = create_free_evening(session, ids, 1, date=dt.date(2026, 1, 10))
    newer = create_free_evening(session, ids, 1, date=dt.date(2026, 3, 5))
    assert get_evening(session, older.id) is older
    assert get_evening(session, 12345) is None
    assert [e.id for e in list_evenings(session)] == [newer.id, older.id]


def test_deleting_evening_removes_seating_but_not_players(session: Session) -> None:
    ids = _register(session, 6)
    evening = create_free_evening(session, ids, 2)
    session.delete(evening)
    session.commit()
    assert session.scalar(select(Seat).limit(1)) is None
    assert len(session.scalars(select(Player)).all()) == 6