import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest


def test_email_is_trimmed() -> None:
    request = LoginRequest(email="  user@example.com  ", password="x")

    assert request.email == "user@example.com"


def test_invalid_email_raises() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(email="not-an-email", password="x")


def test_empty_password_raises() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(email="user@example.com", password="")
