from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.player import PlayerPosition
from app.models.user import User
from tests.factories import make_player, make_user_with_team


def test_my_team_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/players/my-team")

    assert response.status_code == 401


def test_my_team_returns_owned_players(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, team = make_user_with_team(
        db_session, email="owner@b.com", team_name="Owner FC"
    )
    make_player(
        db_session,
        team.id,
        name="Zico",
        position=PlayerPosition.MID,
        passing=90,
    )

    response = client.get("/api/players/my-team", headers=auth_headers(user))

    assert response.status_code == 200
    body = response.json()
    assert body["teamName"] == "Owner FC"
    assert [player["name"] for player in body["players"]] == ["Zico"]
    player = body["players"][0]
    assert player["position"] == "MID"
    assert player["passing"] == 90
    assert "overall" in player
    assert "shirtNumber" not in player


def test_my_team_excludes_other_teams_players(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    owner, _ = make_user_with_team(db_session, email="owner@b.com")
    _, other_team = make_user_with_team(db_session, email="other@b.com")
    make_player(db_session, other_team.id, name="Theirs")

    response = client.get("/api/players/my-team", headers=auth_headers(owner))

    assert response.status_code == 200
    assert response.json()["players"] == []
