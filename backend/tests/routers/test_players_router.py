from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.player import PlayerPosition
from app.models.user import User
from tests.factories import make_player, make_user


def test_my_team_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/players/my-team")

    assert response.status_code == 401


def test_my_team_returns_owned_players(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user = make_user(db_session, email="owner@b.com", team_name="Owner FC")
    make_player(
        db_session,
        user.id,
        name="Zico",
        position=PlayerPosition.CAM,
        shirt_number=10,
    )

    response = client.get("/api/players/my-team", headers=auth_headers(user))

    assert response.status_code == 200
    body = response.json()
    assert body["teamName"] == "Owner FC"
    assert [player["name"] for player in body["players"]] == ["Zico"]
    assert body["players"][0]["shirtNumber"] == 10


def test_my_team_excludes_other_users_players(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    owner = make_user(db_session, email="owner@b.com")
    other = make_user(db_session, email="other@b.com")
    make_player(db_session, other.id, name="Theirs")

    response = client.get("/api/players/my-team", headers=auth_headers(owner))

    assert response.status_code == 200
    assert response.json()["players"] == []
