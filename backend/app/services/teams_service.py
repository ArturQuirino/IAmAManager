import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.team import Team


class TeamsService:
    def __init__(self, db: Session):
        self.db = db

    def find_by_user_id(self, user_id: uuid.UUID) -> Team | None:
        return self.db.scalar(select(Team).where(Team.userId == user_id))

    def create(
        self,
        *,
        team_name: str,
        user_id: uuid.UUID | None = None,
        division_id: uuid.UUID | None = None,
    ) -> Team:
        team = Team(teamName=team_name, userId=user_id, divisionId=division_id)
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team
