from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.schemas.player import MyTeamResponse, PlayerResponse
from app.services.teams_service import TeamsService
from app.services.users_service import PlayersService

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/my-team", response_model=MyTeamResponse)
def get_my_team(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MyTeamResponse:
    teams_service = TeamsService(db)
    players_service = PlayersService(db)

    team = teams_service.find_by_user_id(current_user.user_id)
    if team is None:
        return MyTeamResponse(teamName="", players=[])

    players = players_service.find_by_team_id(team.id)

    return MyTeamResponse(
        teamName=team.teamName,
        players=[PlayerResponse.model_validate(player) for player in players],
    )
