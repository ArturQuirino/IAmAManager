import random
from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.competition_service import CompetitionService
from tests.factories import make_team, make_user, make_user_with_team


def test_standings_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/competition/standings")

    assert response.status_code == 401


def test_standings_empty_when_team_has_no_division(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, _ = make_user_with_team(db_session, email="nodiv@b.com")

    response = client.get(
        "/api/competition/standings", headers=auth_headers(user)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["entries"] == []
    assert body["divisionLevel"] is None


def test_standings_returns_ranked_division_and_flags_own_team(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    service = CompetitionService(db_session, rng=random.Random(1))
    division = service.create_division(level=2, season_number=1)
    user = make_user(db_session, email="owner@b.com")
    mine = make_team(
        db_session,
        user_id=user.id,
        team_name="Mine FC",
        division_id=division.id,
    )
    mine.points = 3
    mine.goalsFor = 2
    mine.goalsAgainst = 2
    rival = make_team(
        db_session, team_name="Rival FC", division_id=division.id
    )
    rival.points = 6
    rival.goalsFor = 5
    rival.goalsAgainst = 1
    db_session.commit()

    response = client.get(
        "/api/competition/standings", headers=auth_headers(user)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["divisionLevel"] == 2
    assert body["seasonNumber"] == 1
    assert [entry["teamName"] for entry in body["entries"]] == [
        "Rival FC",
        "Mine FC",
    ]
    mine_entry = body["entries"][1]
    assert mine_entry["isCurrentUserTeam"] is True
    assert mine_entry["goalDifference"] == 0
    assert body["entries"][0]["isCurrentUserTeam"] is False


def test_standings_exclude_other_divisions(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    service = CompetitionService(db_session, rng=random.Random(1))
    mine_division = service.create_division(level=2)
    other_division = service.create_division(level=1)
    user = make_user(db_session, email="owner@b.com")
    make_team(
        db_session,
        user_id=user.id,
        team_name="Mine FC",
        division_id=mine_division.id,
    )
    make_team(
        db_session, team_name="Elsewhere FC", division_id=other_division.id
    )

    response = client.get(
        "/api/competition/standings", headers=auth_headers(user)
    )

    assert response.status_code == 200
    names = [entry["teamName"] for entry in response.json()["entries"]]
    assert names == ["Mine FC"]
