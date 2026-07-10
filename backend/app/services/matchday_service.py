import logging
import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.division import Division
from app.models.game_clock import GameClock, GameClockId
from app.models.match import Match
from app.models.team import Team
from app.services.match_simulation_service import MatchSimulationService
from app.services.season_service import SeasonService
from app.services.youth_service import YouthService

logger = logging.getLogger(__name__)

# The youth academy refreshes once a week; the season runs one match per day,
# so a "week" is this many matchdays (see docs/players.md, docs/competition.md).
YOUTH_REFRESH_INTERVAL_DAYS = 7


@dataclass
class MatchdayReport:
    """Outcome of a single matchday run, for logging and manual triggering."""

    ran: bool
    matchesPlayed: int = 0
    seasonEnded: bool = False
    youthRefreshed: bool = False


class MatchdayService:
    """Advances the game world by one real day.

    Plays the next unplayed round in every division, then — once every division
    has finished its season — hands off to `SeasonService` for promotion,
    relegation and a fresh fixture list. Runs are idempotent per calendar day
    via the `GameClock` singleton, so the daily scheduler (or a manual trigger)
    can never double-play a day. The clock (a `date` callable) and RNG are
    injectable so the whole cycle is deterministic under test.
    """

    def __init__(
        self,
        db: Session,
        *,
        rng: random.Random | None = None,
        today: Callable[[], date] | None = None,
    ):
        self.db = db
        self._rng = rng or random.Random()
        self._today = today or date.today

    def run_due_matchday(self) -> MatchdayReport:
        """Play today's round unless it has already been played today."""
        today = self._today()
        clock = self._get_or_create_clock()
        if clock.lastMatchdayDate == today:
            logger.info("Matchday already ran for %s; skipping", today)
            return MatchdayReport(ran=False)

        matches_played = self._play_next_round_all_divisions()

        season = SeasonService(self.db)
        season_ended = season.is_pyramid_complete()
        if season_ended:
            season.end_season()

        clock.dayCount += 1
        clock.lastMatchdayDate = today
        youth_refreshed = clock.dayCount % YOUTH_REFRESH_INTERVAL_DAYS == 0
        if youth_refreshed:
            self._refresh_youth_for_user_teams()
        self.db.commit()

        logger.info(
            "Matchday %s: played %s matches (season ended: %s)",
            today,
            matches_played,
            season_ended,
        )
        return MatchdayReport(
            ran=True,
            matchesPlayed=matches_played,
            seasonEnded=season_ended,
            youthRefreshed=youth_refreshed,
        )

    def _play_next_round_all_divisions(self) -> int:
        total = 0
        for division in self._divisions():
            total += self._play_next_round(division)
        return total

    def _play_next_round(self, division: Division) -> int:
        """Simulate the lowest unplayed round of the division's season.

        A team that has been left without a valid starting XI (e.g. its manager
        released a starter) can't be simulated; that single match is skipped and
        logged so it never stalls the rest of the pyramid, and is retried on the
        next matchday.
        """
        next_round = self.db.scalar(
            select(func.min(Match.round)).where(
                Match.divisionId == division.id,
                Match.seasonNumber == division.seasonNumber,
                Match.played.is_(False),
            )
        )
        if next_round is None:
            return 0

        matches = self.db.scalars(
            select(Match).where(
                Match.divisionId == division.id,
                Match.seasonNumber == division.seasonNumber,
                Match.round == next_round,
                Match.played.is_(False),
            )
        ).all()

        simulator = MatchSimulationService(self.db, rng=self._rng)
        played = 0
        for match in matches:
            try:
                simulator.simulate(match)
                played += 1
            except HTTPException:
                logger.warning(
                    "Skipping match %s: a team has no valid starting XI", match.id
                )
        return played

    def _refresh_youth_for_user_teams(self) -> None:
        youth = YouthService(self.db, rng=self._rng)
        for team in self._user_teams():
            youth.refresh_week(team)

    def _divisions(self) -> list[Division]:
        return list(
            self.db.scalars(
                select(Division).order_by(Division.level.asc())
            ).all()
        )

    def _user_teams(self) -> list[Team]:
        return list(
            self.db.scalars(select(Team).where(Team.userId.is_not(None))).all()
        )

    def _get_or_create_clock(self) -> GameClock:
        clock = self.db.get(GameClock, GameClockId.SINGLETON.value)
        if clock is None:
            clock = GameClock(id=GameClockId.SINGLETON.value, dayCount=0)
            self.db.add(clock)
            self.db.flush()
        return clock
