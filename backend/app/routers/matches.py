import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.team import get_current_team
from app.models.match import Match
from app.models.team import Team
from app.schemas.match import (
    MatchDetailResponse,
    MatchEvent,
    MatchListResponse,
    MatchSummary,
)
from app.services.matches_service import MatchesService

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=MatchListResponse)
def list_matches(
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
) -> MatchListResponse:
    matches = MatchesService(db).list_for_team(team)
    return MatchListResponse(
        matches=[_to_summary(match, team) for match in matches]
    )


@router.get("/{match_id}", response_model=MatchDetailResponse)
def get_match(
    match_id: uuid.UUID,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
) -> MatchDetailResponse:
    match = MatchesService(db).get_for_team(team, match_id)
    return _to_detail(match, team)


@router.post("/{match_id}/simulate", response_model=MatchDetailResponse)
def simulate_match(
    match_id: uuid.UUID,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
) -> MatchDetailResponse:
    match = MatchesService(db).simulate_for_team(team, match_id)
    return _to_detail(match, team)


def _to_summary(match: Match, team: Team) -> MatchSummary:
    is_home = match.homeTeamId == team.id
    opponent = match.awayTeam if is_home else match.homeTeam
    return MatchSummary(
        id=match.id,
        round=match.round,
        seasonNumber=match.seasonNumber,
        isHome=is_home,
        opponentTeamId=opponent.id,
        opponentName=opponent.teamName,
        homeScore=match.homeScore,
        awayScore=match.awayScore,
        played=match.played,
        scheduledDate=match.scheduledDate,
    )


def _to_detail(match: Match, team: Team) -> MatchDetailResponse:
    return MatchDetailResponse(
        id=match.id,
        round=match.round,
        seasonNumber=match.seasonNumber,
        isHome=match.homeTeamId == team.id,
        homeTeamId=match.homeTeamId,
        homeTeamName=match.homeTeam.teamName,
        awayTeamId=match.awayTeamId,
        awayTeamName=match.awayTeam.teamName,
        homeScore=match.homeScore,
        awayScore=match.awayScore,
        played=match.played,
        events=[MatchEvent(**event) for event in (match.eventLog or [])],
    )
