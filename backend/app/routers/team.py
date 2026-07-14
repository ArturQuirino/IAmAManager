from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.team import get_current_team
from app.models.team import Team
from app.schemas.team import TeamResponse, UpdateTeamRequest
from app.services.teams_service import TeamsService
from app.services.users_service import PlayersService

router = APIRouter(prefix="/team", tags=["team"])


@router.get("", response_model=TeamResponse)
def get_team(
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
) -> TeamResponse:
    return _to_response(team, PlayersService(db).count_by_team_id(team.id))


@router.patch("", response_model=TeamResponse)
def update_team(
    payload: UpdateTeamRequest,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
) -> TeamResponse:
    TeamsService(db).rename(team, payload.teamName)
    return _to_response(team, PlayersService(db).count_by_team_id(team.id))


def _to_response(team: Team, players_count: int) -> TeamResponse:
    division = team.division
    return TeamResponse(
        teamName=team.teamName,
        divisionLevel=division.level if division else None,
        seasonNumber=division.seasonNumber if division else None,
        played=team.played,
        wins=team.wins,
        draws=team.draws,
        losses=team.losses,
        goalsFor=team.goalsFor,
        goalsAgainst=team.goalsAgainst,
        goalDifference=team.goalDifference,
        points=team.points,
        playersCount=players_count,
    )
