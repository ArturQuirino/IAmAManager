import uuid

import bcrypt
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.player import Player, PlayerPosition
from app.models.user import User

BCRYPT_ROUNDS = 10


class UsersService:
    def __init__(self, db: Session):
        self.db = db

    def find_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def find_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def validate_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )

    def create(self, email: str, plain_password: str) -> User:
        hashed_password = bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt(rounds=BCRYPT_ROUNDS),
        ).decode("utf-8")
        user = User(email=email, password=hashed_password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


class PlayersService:
    def __init__(self, db: Session):
        self.db = db

    def find_by_team_id(self, team_id: uuid.UUID) -> list[Player]:
        return list(
            self.db.scalars(select(Player).where(Player.teamId == team_id)).all()
        )

    def count_by_team_id(self, team_id: uuid.UUID) -> int:
        return self.db.scalar(
            select(func.count()).select_from(Player).where(Player.teamId == team_id)
        ) or 0

    def create(
        self,
        *,
        name: str,
        position: PlayerPosition,
        pace: int,
        shooting: int,
        passing: int,
        dribbling: int,
        defending: int,
        physical: int,
        team_id: uuid.UUID,
        is_starter: bool = False,
    ) -> Player:
        player = Player(
            name=name,
            position=position,
            pace=pace,
            shooting=shooting,
            passing=passing,
            dribbling=dribbling,
            defending=defending,
            physical=physical,
            isStarter=is_starter,
            teamId=team_id,
        )
        self.db.add(player)
        self.db.commit()
        self.db.refresh(player)
        return player

    def add_generated(
        self, team_id: uuid.UUID, players: list[Player]
    ) -> list[Player]:
        """Persist a batch of pre-built (e.g. `PlayerGenerator`) players.

        Assigns each player to the team and commits them in one flush.
        """
        for player in players:
            player.teamId = team_id
        self.db.add_all(players)
        self.db.commit()
        return players
