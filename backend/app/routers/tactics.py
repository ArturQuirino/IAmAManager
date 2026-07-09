from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.team import get_current_team
from app.models.player import Player
from app.models.team import Team
from app.schemas.player import PlayerResponse
from app.schemas.tactics import StartingXiRequest, TacticsResponse
from app.services.tactics_service import TacticsService, derive_formation

router = APIRouter(prefix="/tactics", tags=["tactics"])


@router.get("", response_model=TacticsResponse)
def get_tactics(
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
) -> TacticsResponse:
    starters, bench = TacticsService(db).get_tactics(team)
    return _to_response(starters, bench)


@router.put("/starting-xi", response_model=TacticsResponse)
def set_starting_xi(
    payload: StartingXiRequest,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
) -> TacticsResponse:
    starters, bench = TacticsService(db).set_starting_xi(team, payload.playerIds)
    return _to_response(starters, bench)


def _to_response(
    starters: list[Player], bench: list[Player]
) -> TacticsResponse:
    return TacticsResponse(
        formation=derive_formation(starters),
        starters=[PlayerResponse.model_validate(player) for player in starters],
        bench=[PlayerResponse.model_validate(player) for player in bench],
    )
