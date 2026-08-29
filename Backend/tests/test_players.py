import pytest
from sqlalchemy.orm import Session

from app.services.players import create_player, list_players


def test_create_and_list_sorted(session: Session) -> None:
    create_player(session, "Marco C")
    create_player(session, "Adriano")
    assert [p.name for p in list_players(session)] == ["Adriano", "Marco C"]


def test_name_is_stripped(session: Session) -> None:
    player = create_player(session, "  Luigi P  ")
    assert player.name == "Luigi P"


@pytest.mark.parametrize("name", ["", "   "])
def test_rejects_blank_name(session: Session, name: str) -> None:
    with pytest.raises(ValueError):
        create_player(session, name)


def test_rejects_duplicate_name(session: Session) -> None:
    create_player(session, "Angelo")
    with pytest.raises(ValueError):
        create_player(session, "Angelo")