import re

from pydantic import BaseModel, Field, field_validator

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# Registration input limits. Applied in the schema so invalid input is rejected
# at the boundary (fail fast) before any service work runs.
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
TEAM_NAME_MIN_LENGTH = 2
TEAM_NAME_MAX_LENGTH = 50


def _normalize_email(value: str) -> str:
    normalized = value.strip()
    if not EMAIL_PATTERN.match(normalized):
        raise ValueError("value is not a valid email address")
    return normalized


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(
        min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )
    teamName: str = Field(
        min_length=TEAM_NAME_MIN_LENGTH, max_length=TEAM_NAME_MAX_LENGTH
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)

    @field_validator("teamName")
    @classmethod
    def validate_team_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < TEAM_NAME_MIN_LENGTH:
            raise ValueError("teamName is too short")
        return normalized


class TokenResponse(BaseModel):
    access_token: str
