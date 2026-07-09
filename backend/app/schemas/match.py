import uuid
from datetime import date

from pydantic import BaseModel


class MatchSummary(BaseModel):
    id: uuid.UUID
    round: int
    seasonNumber: int
    # Perspective of the signed-in team: whether it is playing at home, and who
    # it faces. Scores are null until the match has been played.
    isHome: bool
    opponentTeamId: uuid.UUID
    opponentName: str
    homeScore: int | None
    awayScore: int | None
    played: bool
    scheduledDate: date | None


class MatchListResponse(BaseModel):
    matches: list[MatchSummary]


class MatchEvent(BaseModel):
    minute: int
    isHome: bool
    playType: str
    # Stable outcome code (e.g. "goal", "saved"); the frontend narrates it.
    outcome: str
    player: str
    homeScore: int
    awayScore: int


class MatchDetailResponse(BaseModel):
    id: uuid.UUID
    round: int
    seasonNumber: int
    isHome: bool
    homeTeamId: uuid.UUID
    homeTeamName: str
    awayTeamId: uuid.UUID
    awayTeamName: str
    homeScore: int | None
    awayScore: int | None
    played: bool
    # Empty until the match is simulated.
    events: list[MatchEvent]
