import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import conflict
from app.models.team import Team


class TeamsService:
    def __init__(self, db: Session):
        self.db = db

    def find_by_user_id(self, user_id: uuid.UUID) -> Team | None:
        return self.db.scalar(select(Team).where(Team.userId == user_id))

    def find_by_name(
        self, team_name: str, *, exclude_team_id: uuid.UUID | None = None
    ) -> Team | None:
        """Look up a team by name, case-insensitively.

        `exclude_team_id` skips a given team so a rename can be checked for
        collisions without matching the team against itself.
        """
        query = select(Team).where(func.lower(Team.teamName) == team_name.lower())
        if exclude_team_id is not None:
            query = query.where(Team.id != exclude_team_id)
        return self.db.scalar(query)

    def rename(self, team: Team, new_name: str) -> Team:
        """Change a team's name, rejecting a name already taken by another team.

        Team names are unique across the game; a collision (case-insensitive)
        raises a 409 carrying `team.nameAlreadyExists` for the frontend to
        translate.
        """
        if self.find_by_name(new_name, exclude_team_id=team.id) is not None:
            raise conflict("team.nameAlreadyExists")
        team.teamName = new_name
        self.db.commit()
        self.db.refresh(team)
        return team

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
