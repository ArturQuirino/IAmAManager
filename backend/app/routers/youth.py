import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.team import get_current_team
from app.models.team import Team
from app.models.youth_candidate import YouthCandidate
from app.schemas.player import PlayerResponse
from app.schemas.youth import YouthResponse
from app.services.squad_service import MAX_SQUAD_SIZE
from app.services.users_service import PlayersService
from app.services.youth_service import YouthService

router = APIRouter(prefix="/youth", tags=["youth"])


@router.get("", response_model=YouthResponse)
def get_youth(
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
) -> YouthResponse:
    youth_service = YouthService(db)
    candidates = youth_service.get_current(team)
    return _to_response(db, team, candidates)


@router.post("/{candidate_id}/add", response_model=YouthResponse)
def add_youth_player(
    candidate_id: uuid.UUID,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
) -> YouthResponse:
    youth_service = YouthService(db)
    youth_service.add_to_squad(team, candidate_id)
    candidates = youth_service.get_current(team)
    return _to_response(db, team, candidates)


def _to_response(
    db: Session, team: Team, candidates: list[YouthCandidate]
) -> YouthResponse:
    squad_size = PlayersService(db).count_by_team_id(team.id)
    return YouthResponse(
        candidates=[
            PlayerResponse.model_validate(candidate) for candidate in candidates
        ],
        squadSize=squad_size,
        maxSquadSize=MAX_SQUAD_SIZE,
    )
