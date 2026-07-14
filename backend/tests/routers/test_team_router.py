from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.factories import (
    make_division,
    make_squad,
    make_team,
    make_user,
    make_user_with_team,
)


def test_get_team_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/team").status_code == 401


def test_get_team_returns_general_info(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    division = make_division(db_session, level=3, season_number=2)
    user, team = make_user_with_team(db_session, team_name="Owner FC")
    team.divisionId = division.id
    team.points = 9
    team.played = 5
    team.wins = 3
    team.draws = 0
    team.losses = 2
    team.goalsFor = 8
    team.goalsAgainst = 5
    db_session.commit()
    make_squad(db_session, team.id)

    response = client.get("/api/team", headers=auth_headers(user))

    assert response.status_code == 200
    body = response.json()
    assert body["teamName"] == "Owner FC"
    assert body["divisionLevel"] == 3
    assert body["seasonNumber"] == 2
    assert body["points"] == 9
    assert body["goalDifference"] == 3
    assert body["playersCount"] == 11


def test_get_team_without_division_reports_nulls(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, _ = make_user_with_team(db_session)

    response = client.get("/api/team", headers=auth_headers(user))

    assert response.status_code == 200
    body = response.json()
    assert body["divisionLevel"] is None
    assert body["seasonNumber"] is None
    assert body["playersCount"] == 0


def test_update_team_renames(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, _ = make_user_with_team(db_session, team_name="Old Name")

    response = client.patch(
        "/api/team",
        json={"teamName": "  New Name  "},
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["teamName"] == "New Name"


def test_update_team_rejects_a_duplicate_name(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    make_team(db_session, team_name="Taken FC")
    user, _ = make_user_with_team(db_session, team_name="Mine FC")

    response = client.patch(
        "/api/team",
        json={"teamName": "taken fc"},
        headers=auth_headers(user),
    )

    assert response.status_code == 409
    assert response.json()["errorCode"] == "team.nameAlreadyExists"


def test_update_team_keeping_own_name_is_allowed(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, _ = make_user_with_team(db_session, team_name="Same FC")

    response = client.patch(
        "/api/team",
        json={"teamName": "Same FC"},
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["teamName"] == "Same FC"


def test_update_team_rejects_a_too_short_name(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, _ = make_user_with_team(db_session)

    response = client.patch(
        "/api/team", json={"teamName": "a"}, headers=auth_headers(user)
    )

    assert response.status_code == 422


def test_update_team_requires_authentication(client: TestClient) -> None:
    response = client.patch("/api/team", json={"teamName": "Whatever"})
    assert response.status_code == 401


def test_get_team_of_missing_team_is_not_found(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user = make_user(db_session, email="no-team@b.com")

    response = client.get("/api/team", headers=auth_headers(user))

    assert response.status_code == 404
    assert response.json()["errorCode"] == "team.notFound"
