import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.team import get_current_team
from app.models.player import Player
from app.models.team import Team
from app.schemas.player import PlayerResponse
from app.schemas.squad import SquadResponse
from app.services.squad_service import SquadService

router = APIRouter(prefix="/squad", tags=["squad"])


@router.get("", response_model=SquadResponse)
def get_squad(
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
) -> SquadResponse:
    squad_service = SquadService(db)
    return _to_response(team, squad_service.get_squad(team))


@router.delete("/players/{player_id}", response_model=SquadResponse)
def remove_player(
    player_id: uuid.UUID,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
) -> SquadResponse:
    squad_service = SquadService(db)
    squad_service.remove_player(team, player_id)
    return _to_response(team, squad_service.get_squad(team))


def _to_response(team: Team, players: list[Player]) -> SquadResponse:
    return SquadResponse(
        teamName=team.teamName,
        players=[PlayerResponse.model_validate(player) for player in players],
    )
