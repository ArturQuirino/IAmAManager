"""Test data factories.

Small helpers to build persisted `User`/`Player` rows through the real
services (so the bcrypt hashing / column mapping under test is exercised),
independent of the production `seed`.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.player import Player, PlayerPosition
from app.models.user import User
from app.services.users_service import PlayersService, UsersService


def make_user(
    db: Session,
    *,
    email: str = "player@example.com",
    password: str = "secret123",
    team_name: str = "Test FC",
) -> User:
    return UsersService(db).create(
        email=email, plain_password=password, team_name=team_name
    )


def make_player(
    db: Session,
    user_id: uuid.UUID,
    *,
    name: str = "John Doe",
    position: PlayerPosition = PlayerPosition.ST,
    shirt_number: int = 9,
    age: int = 25,
    nationality: str = "Brazil",
    overall: int = 80,
) -> Player:
    return PlayersService(db).create(
        name=name,
        position=position,
        shirt_number=shirt_number,
        age=age,
        nationality=nationality,
        overall=overall,
        user_id=user_id,
    )
