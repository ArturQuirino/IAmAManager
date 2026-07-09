import uuid

from pydantic import BaseModel


class StandingEntry(BaseModel):
    teamId: uuid.UUID
    teamName: str
    played: int
    wins: int
    draws: int
    losses: int
    goalsFor: int
    goalsAgainst: int
    goalDifference: int
    points: int
    # Lets the frontend highlight the row belonging to the signed-in manager.
    isCurrentUserTeam: bool


class StandingsResponse(BaseModel):
    # Null when the team has not been placed in a division yet.
    divisionLevel: int | None = None
    seasonNumber: int | None = None
    entries: list[StandingEntry]
