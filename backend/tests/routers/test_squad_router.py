import uuid
from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.player import PlayerPosition
from app.models.user import User
from tests.factories import make_player, make_squad, make_user_with_team


def test_get_squad_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/squad").status_code == 401


def test_get_squad_returns_owned_players(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, team = make_user_with_team(db_session, team_name="Owner FC")
    make_squad(db_session, team.id)

    response = client.get("/api/squad", headers=auth_headers(user))

    assert response.status_code == 200
    body = response.json()
    assert body["teamName"] == "Owner FC"
    assert len(body["players"]) == 11
    assert body["players"][0]["position"] == "GK"


def test_remove_player_returns_updated_squad(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, team = make_user_with_team(db_session)
    make_squad(db_session, team.id, goalkeepers=1, outfield=11)
    target = make_player(
        db_session, team.id, name="Spare", position=PlayerPosition.MID
    )

    response = client.delete(
        f"/api/squad/players/{target.id}", headers=auth_headers(user)
    )

    assert response.status_code == 200
    names = [player["name"] for player in response.json()["players"]]
    assert "Spare" not in names


def test_remove_last_goalkeeper_is_rejected(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, team = make_user_with_team(db_session)
    keeper = make_player(
        db_session, team.id, name="Only Keeper", position=PlayerPosition.GK
    )
    make_squad(db_session, team.id, goalkeepers=0, outfield=10)

    response = client.delete(
        f"/api/squad/players/{keeper.id}", headers=auth_headers(user)
    )

    assert response.status_code == 409
    assert response.json()["errorCode"] == "squad.minGoalkeeper"


def test_remove_player_of_another_team_is_not_found(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, team = make_user_with_team(db_session, email="owner@b.com")
    make_squad(db_session, team.id)
    _, other = make_user_with_team(db_session, email="other@b.com")
    intruder = make_player(db_session, other.id, name="Theirs")

    response = client.delete(
        f"/api/squad/players/{intruder.id}", headers=auth_headers(user)
    )

    assert response.status_code == 404
    assert response.json()["errorCode"] == "squad.playerNotFound"


def test_remove_requires_authentication(client: TestClient) -> None:
    response = client.delete(f"/api/squad/players/{uuid.uuid4()}")
    assert response.status_code == 401
