from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.schemas.player import MyTeamResponse, PlayerResponse
from app.services.users_service import PlayersService, UsersService

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/my-team", response_model=MyTeamResponse)
def get_my_team(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MyTeamResponse:
    users_service = UsersService(db)
    players_service = PlayersService(db)

    user = users_service.find_by_id(current_user.user_id)
    players = players_service.find_by_user_id(current_user.user_id)

    return MyTeamResponse(
        teamName=user.teamName if user else "Meu Time",
        players=[PlayerResponse.model_validate(player) for player in players],
    )
