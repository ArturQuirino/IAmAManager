import uuid
from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.squad_service import MAX_SQUAD_SIZE
from tests.factories import make_player, make_user_with_team


def test_get_youth_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/youth").status_code == 401


def test_get_youth_returns_four_prospects(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, _ = make_user_with_team(db_session)

    response = client.get("/api/youth", headers=auth_headers(user))

    assert response.status_code == 200
    body = response.json()
    assert len(body["candidates"]) == 4
    assert {candidate["position"] for candidate in body["candidates"]} == {
        "GK",
        "DEF",
        "MID",
        "ATT",
    }
    assert body["maxSquadSize"] == MAX_SQUAD_SIZE
    assert body["squadSize"] == 0


def test_add_youth_player_promotes_and_shrinks_the_pool(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, _ = make_user_with_team(db_session)
    listed = client.get("/api/youth", headers=auth_headers(user)).json()
    candidate_id = listed["candidates"][0]["id"]

    response = client.post(
        f"/api/youth/{candidate_id}/add", headers=auth_headers(user)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["squadSize"] == 1
    assert len(body["candidates"]) == 3
    assert candidate_id not in {c["id"] for c in body["candidates"]}


def test_add_youth_player_when_full_is_rejected(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, team = make_user_with_team(db_session)
    for index in range(MAX_SQUAD_SIZE):
        make_player(db_session, team.id, name=f"P{index}")
    listed = client.get("/api/youth", headers=auth_headers(user)).json()
    candidate_id = listed["candidates"][0]["id"]

    response = client.post(
        f"/api/youth/{candidate_id}/add", headers=auth_headers(user)
    )

    assert response.status_code == 409
    assert response.json()["errorCode"] == "squad.full"


def test_add_unknown_youth_player_is_not_found(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, _ = make_user_with_team(db_session)

    response = client.post(
        f"/api/youth/{uuid.uuid4()}/add", headers=auth_headers(user)
    )

    assert response.status_code == 404
    assert response.json()["errorCode"] == "youth.candidateNotFound"


def test_add_youth_requires_authentication(client: TestClient) -> None:
    response = client.post(f"/api/youth/{uuid.uuid4()}/add")
    assert response.status_code == 401
