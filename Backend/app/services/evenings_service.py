"""Evening creation: orchestrates the seating generator and persistence."""

from __future__ import annotations

import datetime as dt
import random
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.seating import generate_rounds
from app.models import Evening, EveningKind, GameTable, Player, Round, Seat

_SEED_BITS = 31


def create_free_evening(
    session: Session,
    player_ids: Sequence[int],
    n_rounds: int,
    seed: int | None = None,
    date: dt.date | None = None,
) -> Evening:
    """Create a free evening with generated seating for the given players.

    Args:
        session: open database session; the evening is committed before returning.
        player_ids: distinct ids of the participating players.
        n_rounds: number of rounds to generate.
        seed: seating seed; drawn at random and stored when omitted.
        date: evening date; defaults to today.

    Raises:
        ValueError: on unknown or duplicate player ids, or invalid ``n_rounds``.
    """
    ids = list(player_ids)
    if len(set(ids)) != len(ids):
        raise ValueError("Player ids must be unique")
    players = list(session.scalars(select(Player).where(Player.id.in_(ids))))
    if len(players) != len(ids):
        missing = sorted(set(ids) - {p.id for p in players})
        raise ValueError(f"Unknown player ids: {missing}")
    # Keep the caller's order so the generator sees a stable input for a given seed.
    by_id = {p.id: p for p in players}
    ordered = [by_id[i] for i in ids]
    by_name = {p.name: p for p in ordered}

    if seed is None:
        seed = random.getrandbits(_SEED_BITS)
    schedule = generate_rounds([p.name for p in ordered], n_rounds, seed=seed)

    evening = Evening(
        date=date or dt.date.today(),
        kind=EveningKind.FREE,
        n_rounds=n_rounds,
        seed=seed,
    )
    for round_number, tables in enumerate(schedule, start=1):
        round_ = Round(number=round_number)
        for table_number, names in enumerate(tables, start=1):
            table = GameTable(number=table_number)
            table.seats = [
                Seat(player=by_name[name], position=position)
                for position, name in enumerate(names, start=1)
            ]
            round_.tables.append(table)
        evening.rounds.append(round_)

    session.add(evening)
    session.commit()
    return evening


def get_evening(session: Session, evening_id: int) -> Evening | None:
    """Load an evening with its full seating tree, or ``None`` if missing."""
    return session.get(Evening, evening_id)


def list_evenings(session: Session) -> list[Evening]:
    """All evenings, most recent first."""
    return list(session.scalars(select(Evening).order_by(Evening.date.desc(), Evening.id.desc())))


def delete_evening(session: Session, evening_id: int) -> bool:
    """Delete an evening with its seating; return ``False`` if it does not exist."""
    evening = session.get(Evening, evening_id)
    if evening is None:
        return False
    session.delete(evening)
    session.commit()
    return True