from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.exceptions import not_found
from app.models.team import Team
from app.services.teams_service import TeamsService


def get_current_team(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Team:
    """Resolve the signed-in user's team, or 404 if they somehow have none.

    Centralizes the IDOR boundary: downstream services receive the resolved
    `Team` and filter every query by `team.id`, so a client can never reach
    another user's team by passing an id.
    """
    team = TeamsService(db).find_by_user_id(current_user.user_id)
    if team is None:
        raise not_found("team.notFound")
    return team
