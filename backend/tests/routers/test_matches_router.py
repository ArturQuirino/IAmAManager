from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.factories import (
    make_division,
    make_match,
    make_starting_xi,
    make_team,
    make_user_with_team,
)


def _lined_up_match(db: Session):
    """A user with a team plus an opponent, both with a valid XI, and a fixture."""
    division = make_division(db)
    user, team = make_user_with_team(db, team_name="Mine FC")
    team.divisionId = division.id
    opponent = make_team(db, team_name="Rivals FC", division_id=division.id)
    db.commit()
    make_starting_xi(db, team.id, prefix="M")
    make_starting_xi(db, opponent.id, prefix="R")
    match = make_match(
        db, division_id=division.id, home_team_id=team.id, away_team_id=opponent.id
    )
    return user, team, opponent, match


def test_list_matches_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/matches").status_code == 401


def test_simulate_requires_authentication(client: TestClient) -> None:
    assert client.post("/api/matches/whatever/simulate").status_code == 401


def test_list_matches_returns_opponent_perspective(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, _, opponent, _ = _lined_up_match(db_session)

    response = client.get("/api/matches", headers=auth_headers(user))

    assert response.status_code == 200
    matches = response.json()["matches"]
    assert len(matches) == 1
    assert matches[0]["isHome"] is True
    assert matches[0]["opponentName"] == "Rivals FC"
    assert matches[0]["played"] is False
    assert matches[0]["homeScore"] is None


def test_simulate_plays_the_match_and_returns_events(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, _, _, match = _lined_up_match(db_session)

    response = client.post(
        f"/api/matches/{match.id}/simulate", headers=auth_headers(user)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["played"] is True
    assert body["homeScore"] is not None
    assert len(body["events"]) == 91


def test_simulate_rejects_an_already_played_match(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, _, _, match = _lined_up_match(db_session)
    headers = auth_headers(user)
    client.post(f"/api/matches/{match.id}/simulate", headers=headers)

    response = client.post(f"/api/matches/{match.id}/simulate", headers=headers)

    assert response.status_code == 409
    assert response.json()["errorCode"] == "match.alreadyPlayed"


def test_get_match_detail_returns_team_names(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user, _, _, match = _lined_up_match(db_session)

    response = client.get(f"/api/matches/{match.id}", headers=auth_headers(user))

    assert response.status_code == 200
    body = response.json()
    assert body["homeTeamName"] == "Mine FC"
    assert body["awayTeamName"] == "Rivals FC"
    assert body["events"] == []


def test_cannot_access_another_teams_match(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    _, _, _, match = _lined_up_match(db_session)
    # A second, unrelated manager tries to read the fixture.
    intruder, _ = make_user_with_team(db_session, email="intruder@b.com")

    response = client.get(
        f"/api/matches/{match.id}", headers=auth_headers(intruder)
    )

    assert response.status_code == 404
    assert response.json()["errorCode"] == "match.notFound"
