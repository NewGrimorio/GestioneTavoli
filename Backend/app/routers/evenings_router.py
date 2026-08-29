"""Evening endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.models import Evening
from app.routers.deps import get_session
from app.schemas import EveningCreate, EveningRead, EveningSummary, PlayerRead, RoundRead, TableRead
from app.services import evenings_service

router = APIRouter(prefix="/evenings", tags=["evenings"])


def _to_read(evening: Evening) -> EveningRead:
    return EveningRead(
        id=evening.id,
        date=evening.date,
        kind=evening.kind,
        n_rounds=evening.n_rounds,
        seed=evening.seed,
        rounds=[
            RoundRead(
                number=round_.number,
                tables=[
                    TableRead(
                        number=table.number,
                        players=[PlayerRead.model_validate(seat.player) for seat in table.seats],
                    )
                    for table in round_.tables
                ],
            )
            for round_ in evening.rounds
        ],
    )


@router.get("", response_model=list[EveningSummary])
def list_evenings(session: Session = Depends(get_session)) -> list[EveningSummary]:
    return [EveningSummary.model_validate(e) for e in evenings_service.list_evenings(session)]


@router.post("", response_model=EveningRead, status_code=status.HTTP_201_CREATED)
def create_free_evening(body: EveningCreate, session: Session = Depends(get_session)) -> EveningRead:
    try:
        evening = evenings_service.create_free_evening(
            session, body.player_ids, body.n_rounds, seed=body.seed, date=body.date
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return _to_read(evening)


@router.get("/{evening_id}", response_model=EveningRead)
def get_evening(evening_id: int, session: Session = Depends(get_session)) -> EveningRead:
    evening = evenings_service.get_evening(session, evening_id)
    if evening is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evening not found")
    return _to_read(evening)


@router.delete("/{evening_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evening(evening_id: int, session: Session = Depends(get_session)) -> Response:
    if not evenings_service.delete_evening(session, evening_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evening not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
