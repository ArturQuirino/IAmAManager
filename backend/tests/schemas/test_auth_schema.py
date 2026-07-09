import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, RegisterRequest


def test_email_is_trimmed() -> None:
    request = LoginRequest(email="  user@example.com  ", password="x")

    assert request.email == "user@example.com"


def test_invalid_email_raises() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(email="not-an-email", password="x")


def test_empty_password_raises() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(email="user@example.com", password="")


def _valid_register(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "email": "user@example.com",
        "password": "secret123",
        "teamName": "My Club",
    }
    payload.update(overrides)
    return payload


def test_register_trims_email_and_team_name() -> None:
    request = RegisterRequest(
        **_valid_register(email="  user@example.com  ", teamName="  My Club  ")
    )

    assert request.email == "user@example.com"
    assert request.teamName == "My Club"


def test_register_invalid_email_raises() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(**_valid_register(email="not-an-email"))


def test_register_short_password_raises() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(**_valid_register(password="short"))


def test_register_blank_team_name_raises() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(**_valid_register(teamName="   "))


def test_register_too_long_team_name_raises() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(**_valid_register(teamName="x" * 51))
