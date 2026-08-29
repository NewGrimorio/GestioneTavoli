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


def test_create_evening_returns_full_seating(client: TestClient) -> None:
    ids = _register(client, 22)
    response = client.post(
        "/api/evenings",
        json={"player_ids": ids, "n_rounds": 3, "seed": 7, "date": "2026-08-29"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["kind"] == "free"
    assert body["date"] == "2026-08-29"
    assert body["seed"] == 7
    assert [r["number"] for r in body["rounds"]] == [1, 2, 3]
    first = body["rounds"][0]["tables"]
    assert [t["number"] for t in first] == [1, 2, 3, 4, 5, 6]
    assert [len(t["players"]) for t in first] == [4, 4, 4, 4, 3, 3]
    assert set(first[0]["players"][0]) == {"id", "name"}


def test_get_list_and_delete_evening(client: TestClient) -> None:
    ids = _register(client, 6)
    created = client.post("/api/evenings", json={"player_ids": ids, "n_rounds": 2}).json()

    assert client.get(f"/api/evenings/{created['id']}").json() == created
    summaries = client.get("/api/evenings").json()
    assert [s["id"] for s in summaries] == [created["id"]]
    assert "rounds" not in summaries[0]

    assert client.delete(f"/api/evenings/{created['id']}").status_code == 204
    assert client.get(f"/api/evenings/{created['id']}").status_code == 404
    assert client.delete(f"/api/evenings/{created['id']}").status_code == 404


def test_evening_with_unknown_player_is_bad_request(client: TestClient) -> None:
    ids = _register(client, 6)
    response = client.post("/api/evenings", json={"player_ids": ids + [999], "n_rounds": 1})
    assert response.status_code == 400
    assert "999" in response.json()["detail"]


def test_evening_with_too_few_players_is_bad_request(client: TestClient) -> None:
    ids = _register(client, 5)
    response = client.post("/api/evenings", json={"player_ids": ids, "n_rounds": 1})
    assert response.status_code == 400


@pytest.mark.parametrize("payload", [{"n_rounds": 0}, {"n_rounds": 21}, {}])
def test_invalid_round_count_is_validation_error(client: TestClient, payload: dict) -> None:
    ids = _register(client, 6)
    response = client.post("/api/evenings", json={"player_ids": ids, **payload})
    assert response.status_code == 422