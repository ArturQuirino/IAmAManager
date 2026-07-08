from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import make_user


def test_login_success_returns_token(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, email="u@b.com", password="pw123456")

    response = client.post(
        "/api/auth/login", json={"email": "u@b.com", "password": "pw123456"}
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_wrong_password_returns_401(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, email="u@b.com", password="pw123456")

    response = client.post(
        "/api/auth/login", json={"email": "u@b.com", "password": "wrong"}
    )

    assert response.status_code == 401
    assert response.json()["errorCode"] == "auth.invalidCredentials"


def test_login_invalid_email_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"email": "not-an-email", "password": "x"}
    )

    assert response.status_code == 422
