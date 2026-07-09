import random

import pytest
from fastapi import HTTPException
from jose import jwt
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.schemas.auth import LoginRequest, RegisterRequest
from app.models.team import Team
from app.services.auth_service import ALGORITHM, AuthService
from app.services.competition_service import DIVISION_SIZE, CompetitionService
from app.services.teams_service import TeamsService
from app.services.users_service import PlayersService, UsersService
from tests.factories import make_user


def _service(db: Session) -> AuthService:
    """AuthService with a seeded RNG so squad generation is deterministic."""
    return AuthService(db, rng=random.Random(1234))


def _register_request(**overrides: object) -> RegisterRequest:
    payload: dict[str, object] = {
        "email": "manager@example.com",
        "password": "secret123",
        "teamName": "Newcomer FC",
    }
    payload.update(overrides)
    return RegisterRequest(**payload)


def test_validate_user_success(db_session: Session) -> None:
    make_user(db_session, email="u@b.com", password="pw123456")

    user = AuthService(db_session).validate_user("u@b.com", "pw123456")

    assert user is not None
    assert user.email == "u@b.com"


def test_validate_user_wrong_password(db_session: Session) -> None:
    make_user(db_session, email="u@b.com", password="pw123456")

    assert AuthService(db_session).validate_user("u@b.com", "nope") is None


def test_validate_user_unknown_email(db_session: Session) -> None:
    assert AuthService(db_session).validate_user("ghost@b.com", "pw123456") is None


def test_create_access_token_encodes_claims(db_session: Session) -> None:
    user = make_user(db_session, email="u@b.com")

    token = AuthService(db_session).create_access_token(user)

    payload = jwt.decode(
        token, get_settings().jwt_secret, algorithms=[ALGORITHM]
    )
    assert payload["sub"] == str(user.id)
    assert payload["email"] == "u@b.com"
    assert "exp" in payload


def test_login_returns_token(db_session: Session) -> None:
    make_user(db_session, email="u@b.com", password="pw123456")

    response = AuthService(db_session).login(
        LoginRequest(email="u@b.com", password="pw123456")
    )

    assert response.access_token


def test_login_invalid_credentials_raises(db_session: Session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        AuthService(db_session).login(
            LoginRequest(email="ghost@b.com", password="pw123456")
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["errorCode"] == "auth.invalidCredentials"


def test_register_creates_user_team_and_squad(db_session: Session) -> None:
    response = _service(db_session).register(_register_request())

    assert response.access_token
    payload = jwt.decode(
        response.access_token, get_settings().jwt_secret, algorithms=[ALGORITHM]
    )
    assert payload["email"] == "manager@example.com"

    team = _find_team(db_session, "manager@example.com")
    assert team.teamName == "Newcomer FC"
    # A full generated squad: 11 starters + 7 bench.
    assert PlayersService(db_session).count_by_team_id(team.id) == 18


def test_register_places_team_in_lowest_division_with_fakes(
    db_session: Session,
) -> None:
    _service(db_session).register(_register_request())

    team = _find_team(db_session, "manager@example.com")
    assert team.divisionId is not None
    competition = CompetitionService(db_session)
    assert competition.count_teams_in_division(team.divisionId) == DIVISION_SIZE


def test_register_replaces_a_fake_keeping_division_size(
    db_session: Session,
) -> None:
    # Seed a first manager so the lowest division already exists with fakes.
    _service(db_session).register(_register_request())
    competition = CompetitionService(db_session)
    division_id = _find_team(db_session, "manager@example.com").divisionId

    AuthService(db_session, rng=random.Random(99)).register(
        _register_request(email="second@example.com", teamName="Second FC")
    )

    second = _find_team(db_session, "second@example.com")
    assert second.divisionId == division_id
    # Still exactly DIVISION_SIZE: a fake was swapped out, not appended.
    assert competition.count_teams_in_division(division_id) == DIVISION_SIZE


def test_register_duplicate_email_raises_conflict(db_session: Session) -> None:
    make_user(db_session, email="taken@example.com")

    with pytest.raises(HTTPException) as exc_info:
        _service(db_session).register(
            _register_request(email="taken@example.com")
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["errorCode"] == "auth.emailAlreadyExists"


def _find_team(db: Session, email: str) -> Team:
    user = UsersService(db).find_by_email(email)
    assert user is not None
    team = TeamsService(db).find_by_user_id(user.id)
    assert team is not None
    return team
