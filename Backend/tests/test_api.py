from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(db_path=None)
    with TestClient(app) as client:
        yield client
    app.state.engine.dispose()


def _register(client: TestClient, n: int) -> list[int]:
    ids = []
    for i in range(n):
        response = client.post("/api/players", json={"name": f"P{i:02d}"})
        assert response.status_code == 201, response.text
        ids.append(response.json()["id"])
    return ids


def _session_with(client: TestClient, n: int, n_rounds: int = 3) -> dict:
    session = client.post("/api/sessions", json={"n_rounds": n_rounds}).json()
    for player_id in _register(client, n):
        response = client.post(
            f"/api/sessions/{session['id']}/participants", json={"player_id": player_id}
        )
        assert response.status_code == 201, response.text
    return client.get(f"/api/sessions/{session['id']}").json()


# --------------------------------------------------------------------------- #
# meta / players
# --------------------------------------------------------------------------- #


def test_health(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_create_and_list_players(client: TestClient) -> None:
    client.post("/api/players", json={"name": "Marco C"})
    client.post("/api/players", json={"name": "Adriano"})
    names = [p["name"] for p in client.get("/api/players").json()]
    assert names == ["Adriano", "Marco C"]


def test_duplicate_player_is_conflict(client: TestClient) -> None:
    client.post("/api/players", json={"name": "Angelo"})
    assert client.post("/api/players", json={"name": "Angelo"}).status_code == 409


def test_blank_player_name_is_rejected(client: TestClient) -> None:
    assert client.post("/api/players", json={"name": ""}).status_code == 422


# --------------------------------------------------------------------------- #
# sessions
# --------------------------------------------------------------------------- #


def test_create_session_is_open_and_empty(client: TestClient) -> None:
    response = client.post("/api/sessions", json={"n_rounds": 3, "date": "2026-08-29"})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "open"
    assert body["kind"] == "free"
    assert body["date"] == "2026-08-29"
    assert body["seed"] is None
    assert body["n_participants"] == 0
    assert body["tables_generated"] is False
    assert body["participants"] == []
    assert body["rounds"] == []


def test_current_session(client: TestClient) -> None:
    assert client.get("/api/sessions/current").status_code == 404
    created = client.post("/api/sessions", json={"n_rounds": 1}).json()
    assert client.get("/api/sessions/current").json()["id"] == created["id"]


def test_new_session_closes_previous(client: TestClient) -> None:
    first = client.post("/api/sessions", json={"n_rounds": 1}).json()
    second = client.post("/api/sessions", json={"n_rounds": 1}).json()
    assert client.get(f"/api/sessions/{first['id']}").json()["status"] == "closed"
    assert client.get("/api/sessions/current").json()["id"] == second["id"]


def test_list_has_summaries_only(client: TestClient) -> None:
    _session_with(client, 6)
    summaries = client.get("/api/sessions").json()
    assert len(summaries) == 1
    assert summaries[0]["n_participants"] == 6
    assert "rounds" not in summaries[0]
    assert "participants" not in summaries[0]


def test_participants_are_returned_alphabetically(client: TestClient) -> None:
    session = client.post("/api/sessions", json={"n_rounds": 1}).json()
    for name in ["marco", "Adriano", "Luigi"]:
        player = client.post("/api/players", json={"name": name}).json()
        client.post(f"/api/sessions/{session['id']}/participants", json={"player_id": player["id"]})
    body = client.get(f"/api/sessions/{session['id']}").json()
    assert [p["name"] for p in body["participants"]] == ["Adriano", "Luigi", "marco"]


def test_add_unknown_player_is_not_found(client: TestClient) -> None:
    session = client.post("/api/sessions", json={"n_rounds": 1}).json()
    response = client.post(f"/api/sessions/{session['id']}/participants", json={"player_id": 999})
    assert response.status_code == 404


def test_add_same_player_twice_is_conflict(client: TestClient) -> None:
    session = client.post("/api/sessions", json={"n_rounds": 1}).json()
    (player_id,) = _register(client, 1)
    url = f"/api/sessions/{session['id']}/participants"
    assert client.post(url, json={"player_id": player_id}).status_code == 201
    assert client.post(url, json={"player_id": player_id}).status_code == 409


def test_remove_participant(client: TestClient) -> None:
    session = _session_with(client, 2)
    player_id = session["participants"][0]["id"]
    response = client.delete(f"/api/sessions/{session['id']}/participants/{player_id}")
    assert response.status_code == 200
    assert response.json()["n_participants"] == 1
    response = client.delete(f"/api/sessions/{session['id']}/participants/{player_id}")
    assert response.status_code == 404


def test_generate_tables(client: TestClient) -> None:
    session = _session_with(client, 22, n_rounds=3)
    response = client.post(f"/api/sessions/{session['id']}/generate", json={"seed": 7})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tables_generated"] is True
    assert body["seed"] == 7
    assert [r["number"] for r in body["rounds"]] == [1, 2, 3]
    first = body["rounds"][0]["tables"]
    assert [len(t["players"]) for t in first] == [4, 4, 4, 4, 3, 3]


def test_generate_without_body_draws_seed(client: TestClient) -> None:
    session = _session_with(client, 6)
    body = client.post(f"/api/sessions/{session['id']}/generate").json()
    assert isinstance(body["seed"], int)


def test_generate_with_too_few_participants_is_bad_request(client: TestClient) -> None:
    session = _session_with(client, 5)
    assert client.post(f"/api/sessions/{session['id']}/generate").status_code == 400


def test_generate_twice_is_conflict(client: TestClient) -> None:
    session = _session_with(client, 6)
    assert client.post(f"/api/sessions/{session['id']}/generate").status_code == 200
    assert client.post(f"/api/sessions/{session['id']}/generate").status_code == 409


def test_latecomer_after_generation_is_conflict(client: TestClient) -> None:
    session = _session_with(client, 6)
    client.post(f"/api/sessions/{session['id']}/generate")
    late = client.post("/api/players", json={"name": "Late"}).json()
    response = client.post(
        f"/api/sessions/{session['id']}/participants", json={"player_id": late["id"]}
    )
    assert response.status_code == 409


def test_close_and_delete(client: TestClient) -> None:
    session = _session_with(client, 6)
    assert client.post(f"/api/sessions/{session['id']}/close").json()["status"] == "closed"
    assert client.post(f"/api/sessions/{session['id']}/close").status_code == 409
    assert client.get("/api/sessions/current").status_code == 404
    assert client.delete(f"/api/sessions/{session['id']}").status_code == 204
    assert client.get(f"/api/sessions/{session['id']}").status_code == 404
    assert client.delete(f"/api/sessions/{session['id']}").status_code == 404


@pytest.mark.parametrize("payload", [{"n_rounds": 0}, {"n_rounds": 21}, {}])
def test_invalid_round_count_is_validation_error(client: TestClient, payload: dict) -> None:
    assert client.post("/api/sessions", json=payload).status_code == 422
