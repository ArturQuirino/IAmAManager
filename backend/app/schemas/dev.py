from pydantic import BaseModel


class MatchdayReportResponse(BaseModel):
    """Result of manually triggering a matchday (development only)."""

    # False when the matchday had already been played for the current day.
    ran: bool
    matchesPlayed: int
    seasonEnded: bool
    youthRefreshed: bool
