import pytest
from sqlalchemy.orm import Session as DbSession

from app.services.players_service import create_player, list_players


def test_create_and_list_sorted(db: DbSession) -> None:
    create_player(db, "Marco C")
    create_player(db, "Adriano")
    assert [p.name for p in list_players(db)] == ["Adriano", "Marco C"]


def test_name_is_stripped(db: DbSession) -> None:
    player = create_player(db, "  Luigi P  ")
    assert player.name == "Luigi P"


@pytest.mark.parametrize("name", ["", "   "])
def test_rejects_blank_name(db: DbSession, name: str) -> None:
    with pytest.raises(ValueError):
        create_player(db, name)


def test_rejects_duplicate_name(db: DbSession) -> None:
    create_player(db, "Angelo")
    with pytest.raises(ValueError):
        create_player(db, "Angelo")
