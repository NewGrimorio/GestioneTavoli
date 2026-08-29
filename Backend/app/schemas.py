"""Pydantic schemas: the JSON shapes exchanged with the frontend."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.models import SessionKind, SessionStatus


class PlayerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class PlayerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class SessionCreate(BaseModel):
    n_rounds: int = Field(ge=1, le=20)
    date: dt.date | None = None


class ParticipantAdd(BaseModel):
    player_id: int


class GenerateTables(BaseModel):
    seed: int | None = None


class TableRead(BaseModel):
    number: int
    players: list[PlayerRead]


class RoundRead(BaseModel):
    number: int
    tables: list[TableRead]


class SessionSummary(BaseModel):
    id: int
    date: dt.date
    kind: SessionKind
    status: SessionStatus
    n_rounds: int
    seed: int | None
    n_participants: int
    tables_generated: bool


class SessionRead(SessionSummary):
    participants: list[PlayerRead]
    rounds: list[RoundRead]
