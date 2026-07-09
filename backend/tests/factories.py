"""Test data factories.

Small helpers to build persisted `User`/`Team`/`Player` rows through the real
services (so the bcrypt hashing / column mapping under test is exercised),
independent of the production `seed`.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.player import Player, PlayerPosition
from app.models.team import Team
from app.models.user import User
from app.services.teams_service import TeamsService
from app.services.users_service import PlayersService, UsersService


def make_user(
    db: Session,
    *,
    email: str = "player@example.com",
    password: str = "secret123",
) -> User:
    return UsersService(db).create(email=email, plain_password=password)


def make_team(
    db: Session,
    *,
    user_id: uuid.UUID | None = None,
    team_name: str = "Test FC",
    division_id: uuid.UUID | None = None,
) -> Team:
    return TeamsService(db).create(
        team_name=team_name, user_id=user_id, division_id=division_id
    )


def make_user_with_team(
    db: Session,
    *,
    email: str = "player@example.com",
    password: str = "secret123",
    team_name: str = "Test FC",
) -> tuple[User, Team]:
    user = make_user(db, email=email, password=password)
    team = make_team(db, user_id=user.id, team_name=team_name)
    return user, team


def make_player(
    db: Session,
    team_id: uuid.UUID,
    *,
    name: str = "John Doe",
    position: PlayerPosition = PlayerPosition.ATT,
    pace: int = 70,
    shooting: int = 70,
    passing: int = 70,
    dribbling: int = 70,
    defending: int = 70,
    physical: int = 70,
    is_starter: bool = False,
) -> Player:
    return PlayersService(db).create(
        name=name,
        position=position,
        pace=pace,
        shooting=shooting,
        passing=passing,
        dribbling=dribbling,
        defending=defending,
        physical=physical,
        team_id=team_id,
        is_starter=is_starter,
    )


_OUTFIELD_CYCLE = (PlayerPosition.DEF, PlayerPosition.MID, PlayerPosition.ATT)


def make_squad(
    db: Session,
    team_id: uuid.UUID,
    *,
    goalkeepers: int = 1,
    outfield: int = 10,
) -> None:
    """Populate a team with a valid minimum squad (1 GK + 10 outfield)."""
    for index in range(goalkeepers):
        make_player(db, team_id, name=f"GK{index}", position=PlayerPosition.GK)
    for index in range(outfield):
        make_player(
            db,
            team_id,
            name=f"OUT{index}",
            position=_OUTFIELD_CYCLE[index % len(_OUTFIELD_CYCLE)],
        )
