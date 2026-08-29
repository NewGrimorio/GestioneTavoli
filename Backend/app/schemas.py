"""Pydantic schemas: the JSON shapes exchanged with the frontend."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.models import EveningKind


class PlayerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class PlayerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class EveningCreate(BaseModel):
    player_ids: list[int] = Field(min_length=1)
    n_rounds: int = Field(ge=1, le=20)
    seed: int | None = None
    date: dt.date | None = None


class TableRead(BaseModel):
    number: int
    players: list[PlayerRead]


class RoundRead(BaseModel):
    number: int
    tables: list[TableRead]


class EveningSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: dt.date
    kind: EveningKind
    n_rounds: int
    seed: int


class EveningRead(EveningSummary):
    rounds: list[RoundRead]