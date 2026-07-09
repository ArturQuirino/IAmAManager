import uuid
from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.player import Player, PlayerPosition
from app.models.user import User
from tests.factories import make_player, make_user_with_team


def _valid_xi(db: Session, team_id: uuid.UUID) -> list[Player]:
    players = [make_player(db, team_id, name="GK", position=PlayerPosition.GK)]
    lines = (
        [PlayerPosition.DEF] * 4
        + [PlayerPosition.MID] * 3
        + [PlayerPosition.ATT] * 3
    )
    for index, position in enumerate(lines):
        players.append(
            make_player(db, team_id, name=f"P{index}", position=position)
        )
    return players


def test_get_tactics_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/tactics").status_code == 401


def test_set_starting_xi_requires_authentication(client: TestClient) -> None:
    response = client.put("/api/tactics/starting-xi", json={"playerIds": []})
    assert response.status_code == 401


def test_get_tactics_returns_starters_bench_and_formation(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, team = make_user_with_team(db_session)
    xi = _valid_xi(db_session, team.id)
    make_player(db_session, team.id, name="Reserve", position=PlayerPosition.ATT)
    client.put(
        "/api/tactics/starting-xi",
        headers=auth_headers(user),
        json={"playerIds": [str(player.id) for player in xi]},
    )

    response = client.get("/api/tactics", headers=auth_headers(user))

    assert response.status_code == 200
    body = response.json()
    assert body["formation"] == "4-3-3"
    assert len(body["starters"]) == 11
    assert [player["name"] for player in body["bench"]] == ["Reserve"]


def test_set_starting_xi_persists_and_returns_updated(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, team = make_user_with_team(db_session)
    xi = _valid_xi(db_session, team.id)

    response = client.put(
        "/api/tactics/starting-xi",
        headers=auth_headers(user),
        json={"playerIds": [str(player.id) for player in xi]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["formation"] == "4-3-3"
    assert len(body["starters"]) == 11
    assert body["bench"] == []


def test_set_starting_xi_rejects_wrong_count(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, team = make_user_with_team(db_session)
    xi = _valid_xi(db_session, team.id)

    response = client.put(
        "/api/tactics/starting-xi",
        headers=auth_headers(user),
        json={"playerIds": [str(player.id) for player in xi[:10]]},
    )

    assert response.status_code == 422
    assert response.json()["errorCode"] == "tactics.mustBe11"


def test_set_starting_xi_rejects_missing_goalkeeper(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, team = make_user_with_team(db_session)
    outfield = [
        make_player(db_session, team.id, name=f"O{i}", position=PlayerPosition.MID)
        for i in range(11)
    ]

    response = client.put(
        "/api/tactics/starting-xi",
        headers=auth_headers(user),
        json={"playerIds": [str(player.id) for player in outfield]},
    )

    assert response.status_code == 422
    assert response.json()["errorCode"] == "tactics.needExactlyOneGk"


def test_set_starting_xi_rejects_another_teams_player(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, team = make_user_with_team(db_session, email="owner@b.com")
    _, other = make_user_with_team(db_session, email="other@b.com")
    xi = _valid_xi(db_session, team.id)
    intruder = make_player(db_session, other.id, name="Theirs")
    ids = [str(player.id) for player in xi[:10]] + [str(intruder.id)]

    response = client.put(
        "/api/tactics/starting-xi",
        headers=auth_headers(user),
        json={"playerIds": ids},
    )

    assert response.status_code == 404
    assert response.json()["errorCode"] == "tactics.playerNotFound"
