"""Player registry operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Player


def create_player(session: Session, name: str) -> Player:
    """Register a new player.

    Raises:
        ValueError: if ``name`` is blank or already taken.
    """
    clean = name.strip()
    if not clean:
        raise ValueError("Player name cannot be empty")
    if session.scalar(select(Player).where(Player.name == clean)) is not None:
        raise ValueError(f"Player {clean!r} already exists")
    player = Player(name=clean)
    session.add(player)
    session.commit()
    return player


def list_players(session: Session) -> list[Player]:
    """All players, alphabetically."""
    return list(session.scalars(select(Player).order_by(Player.name)))
