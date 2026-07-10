from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.division import Division
from app.models.match import Match
from app.models.team import Team
from app.services.competition_service import STANDING_FIELDS, CompetitionService
from app.services.schedule_service import ScheduleService

# End-of-season movement between adjacent divisions (see docs/competition.md):
# the top two are promoted, the bottom two relegated. The counts are equal so
# every division stays at exactly DIVISION_SIZE across a turnover.
PROMOTION_SLOTS = 2
RELEGATION_SLOTS = 2


@dataclass
class DivisionOutcome:
    """What happened to one division at the end of a season."""

    divisionId: object
    level: int
    seasonNumber: int
    championTeamId: object | None
    promotedTeamIds: list[object] = field(default_factory=list)
    relegatedTeamIds: list[object] = field(default_factory=list)


class SeasonService:
    """End-of-season turnover for the whole division pyramid.

    A season ends when every division has played all its fixtures; since the
    daily job advances every division in lockstep, that happens on the same day
    across the pyramid, so turnover is a single pyramid-wide event rather than a
    per-division one. It promotes/relegates between adjacent tiers, resets the
    standings, advances the season number and lays out fresh fixtures.
    """

    def __init__(self, db: Session):
        self.db = db
        self._competition = CompetitionService(db)

    def is_division_complete(self, division: Division) -> bool:
        """Whether the division has fixtures this season and all are played."""
        total, unplayed = self._match_counts(division)
        return total > 0 and unplayed == 0

    def is_pyramid_complete(self) -> bool:
        """Whether every division has finished its current season."""
        divisions = self._divisions_by_level()
        return bool(divisions) and all(
            self.is_division_complete(division) for division in divisions
        )

    def end_season(self) -> list[DivisionOutcome]:
        """Run promotion/relegation, reset standings and open the next season.

        Standings are snapshotted before any team moves, so promotions and
        relegations are computed from the final table and applied atomically.
        Returns a per-division summary (champion and the teams that moved).
        """
        divisions = self._divisions_by_level()
        if not divisions:
            return []

        level_index = {division.level: division for division in divisions}
        standings = {
            division.id: self._competition.get_division_standings(division.id)
            for division in divisions
        }
        outcomes = self._build_outcomes(divisions, level_index, standings)

        self._apply_movements(divisions, level_index, standings)
        self._reset_and_advance(divisions, standings)
        self.db.commit()

        for division in divisions:
            ScheduleService(self.db).generate_double_round_robin(division)
        return outcomes

    def _build_outcomes(
        self,
        divisions: list[Division],
        level_index: dict[int, Division],
        standings: dict[object, list[Team]],
    ) -> list[DivisionOutcome]:
        outcomes: list[DivisionOutcome] = []
        for division in divisions:
            promoted, relegated = self._movers(division, level_index, standings)
            table = standings[division.id]
            outcomes.append(
                DivisionOutcome(
                    divisionId=division.id,
                    level=division.level,
                    seasonNumber=division.seasonNumber,
                    championTeamId=table[0].id if table else None,
                    promotedTeamIds=[team.id for team in promoted],
                    relegatedTeamIds=[team.id for team in relegated],
                )
            )
        return outcomes

    def _apply_movements(
        self,
        divisions: list[Division],
        level_index: dict[int, Division],
        standings: dict[object, list[Team]],
    ) -> None:
        for division in divisions:
            promoted, relegated = self._movers(division, level_index, standings)
            for team in promoted:
                team.divisionId = level_index[division.level - 1].id
            for team in relegated:
                team.divisionId = level_index[division.level + 1].id

    def _movers(
        self,
        division: Division,
        level_index: dict[int, Division],
        standings: dict[object, list[Team]],
    ) -> tuple[list[Team], list[Team]]:
        """The teams promoted (up) and relegated (down) from this division.

        A division only promotes if a tier above it exists, and only relegates
        if a tier below it exists — so the top never promotes and the lowest
        never relegates. Overlapping picks in a pathologically small division
        favour promotion, so no team is moved twice.
        """
        table = standings[division.id]
        promoted = (
            table[:PROMOTION_SLOTS]
            if (division.level - 1) in level_index and len(table) >= PROMOTION_SLOTS
            else []
        )
        relegated = (
            table[-RELEGATION_SLOTS:]
            if (division.level + 1) in level_index and len(table) >= RELEGATION_SLOTS
            else []
        )
        promoted_ids = {team.id for team in promoted}
        relegated = [team for team in relegated if team.id not in promoted_ids]
        return promoted, relegated

    def _reset_and_advance(
        self, divisions: list[Division], standings: dict[object, list[Team]]
    ) -> None:
        for teams in standings.values():
            for team in teams:
                for field_name in STANDING_FIELDS:
                    setattr(team, field_name, 0)
        for division in divisions:
            division.seasonNumber += 1

    def _divisions_by_level(self) -> list[Division]:
        return list(
            self.db.scalars(
                select(Division).order_by(Division.level.asc())
            ).all()
        )

    def _match_counts(self, division: Division) -> tuple[int, int]:
        """(total, unplayed) match counts for the division's current season."""
        base = (
            select(func.count())
            .select_from(Match)
            .where(
                Match.divisionId == division.id,
                Match.seasonNumber == division.seasonNumber,
            )
        )
        total = self.db.scalar(base) or 0
        unplayed = self.db.scalar(base.where(Match.played.is_(False))) or 0
        return total, unplayed
