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


def _register_payload(**overrides: str) -> dict[str, str]:
    payload = {
        "email": "manager@example.com",
        "password": "secret123",
        "teamName": "Newcomer FC",
    }
    payload.update(overrides)
    return payload


def test_register_success_returns_token_and_201(client: TestClient) -> None:
    response = client.post("/api/auth/register", json=_register_payload())

    assert response.status_code == 201
    assert response.json()["access_token"]


def test_register_logs_the_new_manager_in(
    client: TestClient, db_session: Session
) -> None:
    register = client.post("/api/auth/register", json=_register_payload())
    token = register.json()["access_token"]

    my_team = client.get(
        "/api/players/my-team",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert my_team.status_code == 200
    body = my_team.json()
    assert body["teamName"] == "Newcomer FC"
    assert len(body["players"]) == 18


def test_register_duplicate_email_returns_409(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, email="taken@example.com")

    response = client.post(
        "/api/auth/register", json=_register_payload(email="taken@example.com")
    )

    assert response.status_code == 409
    assert response.json()["errorCode"] == "auth.emailAlreadyExists"


def test_register_short_password_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register", json=_register_payload(password="short")
    )

    assert response.status_code == 422
