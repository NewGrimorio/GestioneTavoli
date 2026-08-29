"""Player endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.routers.deps import get_session
from app.schemas import PlayerCreate, PlayerRead
from app.services import players_service

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=list[PlayerRead])
def list_players(session: Session = Depends(get_session)) -> list[PlayerRead]:
    return [PlayerRead.model_validate(p) for p in players_service.list_players(session)]


@router.post("", response_model=PlayerRead, status_code=status.HTTP_201_CREATED)
def create_player(body: PlayerCreate, session: Session = Depends(get_session)) -> PlayerRead:
    try:
        player = players_service.create_player(session, body.name)
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return PlayerRead.model_validate(player)
