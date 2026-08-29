"""Player registry operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models import Player


def create_player(db: DbSession, name: str) -> Player:
    """Register a new player.

    Raises:
        ValueError: if ``name`` is blank or already taken.
    """
    clean = name.strip()
    if not clean:
        raise ValueError("Player name cannot be empty")
    if db.scalar(select(Player).where(Player.name == clean)) is not None:
        raise ValueError(f"Player {clean!r} already exists")
    player = Player(name=clean)
    db.add(player)
    db.commit()
    return player


def list_players(db: DbSession) -> list[Player]:
    """All players, alphabetically."""
    return list(db.scalars(select(Player).order_by(Player.name)))
