import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.models.team import Team
from app.schemas.competition import StandingEntry, StandingsResponse
from app.services.competition_service import CompetitionService
from app.services.teams_service import TeamsService

router = APIRouter(prefix="/competition", tags=["competition"])


@router.get("/standings", response_model=StandingsResponse)
def get_standings(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StandingsResponse:
    teams_service = TeamsService(db)
    competition = CompetitionService(db)

    team = teams_service.find_by_user_id(current_user.user_id)
    if team is None or team.divisionId is None:
        return StandingsResponse(entries=[])

    division = competition.get_division(team.divisionId)
    standings = competition.get_division_standings(team.divisionId)

    return StandingsResponse(
        divisionLevel=division.level if division else None,
        seasonNumber=division.seasonNumber if division else None,
        entries=[_to_entry(row, current_team_id=team.id) for row in standings],
    )


def _to_entry(team: Team, *, current_team_id: uuid.UUID) -> StandingEntry:
    return StandingEntry(
        teamId=team.id,
        teamName=team.teamName,
        played=team.played,
        wins=team.wins,
        draws=team.draws,
        losses=team.losses,
        goalsFor=team.goalsFor,
        goalsAgainst=team.goalsAgainst,
        goalDifference=team.goalDifference,
        points=team.points,
        isCurrentUserTeam=team.id == current_team_id,
    )
