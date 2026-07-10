from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.schedule_service import ScheduleService
from tests.factories import make_division, make_starting_xi, make_team, make_user_with_team


def _ready_world(db: Session) -> User:
    """A single division with a user team and a fake opponent, plus fixtures."""
    division = make_division(db, level=1)
    user, team = make_user_with_team(db, team_name="Mine FC")
    team.divisionId = division.id
    opponent = make_team(db, team_name="Rival FC", division_id=division.id)
    db.commit()
    make_starting_xi(db, team.id, prefix="M")
    make_starting_xi(db, opponent.id, prefix="R")
    ScheduleService(db).generate_double_round_robin(division)
    return user


def test_run_matchday_requires_authentication(client: TestClient) -> None:
    assert client.post("/api/dev/run-matchday").status_code == 401


def test_run_matchday_plays_the_days_round(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user = _ready_world(db_session)

    response = client.post(
        "/api/dev/run-matchday", headers=auth_headers(user)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ran"] is True
    assert body["matchesPlayed"] == 1
    assert body["seasonEnded"] is False


def test_run_matchday_is_idempotent_within_the_day(
    client: TestClient,
    db_session: Session,
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    user = _ready_world(db_session)
    headers = auth_headers(user)
    client.post("/api/dev/run-matchday", headers=headers)

    response = client.post("/api/dev/run-matchday", headers=headers)

    assert response.status_code == 200
    assert response.json()["ran"] is False
