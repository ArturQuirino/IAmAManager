import pytest
from fastapi import HTTPException
from jose import jwt
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.schemas.auth import LoginRequest
from app.services.auth_service import ALGORITHM, AuthService
from tests.factories import make_user


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
    assert exc_info.value.detail["message"] == "Credenciais inválidas"
