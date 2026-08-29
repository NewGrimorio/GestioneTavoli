"""ORM entities.

Tree of a session:
    Session -> Participant -> Player        (who signed up, before tables exist)
    Session -> Round -> GameTable -> Seat -> Player   (actual seating, once generated)

``Seat`` is the leaf: one row per player per table. Per-round scores will live
there when ranked sessions are introduced.
"""

from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SessionKind(enum.StrEnum):
    FREE = "free"
    RANKED = "ranked"


class SessionStatus(enum.StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class Player(Base):
    """A person of the group. ``name`` is a free label: full name or nickname."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)


class Session(Base):
    """One game night. At most one session is ``OPEN`` at any time."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    kind: Mapped[SessionKind] = mapped_column(Enum(SessionKind), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), nullable=False)
    n_rounds: Mapped[int] = mapped_column(Integer, nullable=False)
    # Seed used to generate the seating; ``None`` until tables are generated,
    # then always stored so a schedule can be replayed.
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)

    participants: Mapped[list[Participant]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Participant.id",
    )
    rounds: Mapped[list[Round]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Round.number",
    )

    @property
    def tables_generated(self) -> bool:
        return len(self.rounds) > 0


class Participant(Base):
    """A player signed up for a session."""

    __tablename__ = "participants"
    __table_args__ = (UniqueConstraint("session_id", "player_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="RESTRICT"), nullable=False
    )

    session: Mapped[Session] = relationship(back_populates="participants")
    player: Mapped[Player] = relationship()


class Round(Base):
    __tablename__ = "rounds"
    __table_args__ = (UniqueConstraint("session_id", "number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)

    session: Mapped[Session] = relationship(back_populates="rounds")
    tables: Mapped[list[GameTable]] = relationship(
        back_populates="round",
        cascade="all, delete-orphan",
        order_by="GameTable.number",
    )


class GameTable(Base):
    """A table within a round. Named ``GameTable`` to avoid clashing with ``sqlalchemy.Table``."""

    __tablename__ = "tables"
    __table_args__ = (UniqueConstraint("round_id", "number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    round_id: Mapped[int] = mapped_column(
        ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)

    round: Mapped[Round] = relationship(back_populates="tables")
    seats: Mapped[list[Seat]] = relationship(
        back_populates="table",
        cascade="all, delete-orphan",
        order_by="Seat.position",
    )


class Seat(Base):
    __tablename__ = "seats"

    table_id: Mapped[int] = mapped_column(
        ForeignKey("tables.id", ondelete="CASCADE"), primary_key=True
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="RESTRICT"), primary_key=True
    )
    # Order of the player within the table, as produced by the generator.
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    table: Mapped[GameTable] = relationship(back_populates="seats")
    player: Mapped[Player] = relationship()
