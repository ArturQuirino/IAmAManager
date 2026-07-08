import uuid

import bcrypt
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.player import Player, PlayerPosition
from app.models.user import User


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

    def create(self, email: str, plain_password: str, team_name: str) -> User:
        hashed_password = bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt(rounds=10),
        ).decode("utf-8")
        user = User(email=email, password=hashed_password, teamName=team_name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


class PlayersService:
    def __init__(self, db: Session):
        self.db = db

    def find_by_user_id(self, user_id: uuid.UUID) -> list[Player]:
        return list(
            self.db.scalars(select(Player).where(Player.userId == user_id)).all()
        )

    def count_by_user_id(self, user_id: uuid.UUID) -> int:
        return self.db.scalar(
            select(func.count()).select_from(Player).where(Player.userId == user_id)
        ) or 0

    def create(
        self,
        *,
        name: str,
        position: PlayerPosition,
        shirt_number: int,
        age: int,
        nationality: str,
        overall: int,
        user_id: uuid.UUID,
    ) -> Player:
        player = Player(
            name=name,
            position=position,
            shirtNumber=shirt_number,
            age=age,
            nationality=nationality,
            overall=overall,
            userId=user_id,
        )
        self.db.add(player)
        self.db.commit()
        self.db.refresh(player)
        return player
