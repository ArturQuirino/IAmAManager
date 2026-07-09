import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.division import Division
from app.models.match import Match
from app.models.team import Team

# Number of legs each pair of teams plays in a season: one home, one away.
LEGS = 2


class ScheduleService:
    """Builds a division's season fixture list (a double round-robin).

    Every team plays every other twice — once home, once away — spread over
    2×(n−1) rounds via the circle method (docs/competition.md): for 10 teams
    that is 18 rounds of 5 matches. No business state beyond the fixtures is
    touched; simulation and standings live in their own services.
    """

    def __init__(self, db: Session):
        self.db = db

    def has_fixtures(self, division: Division) -> bool:
        """Whether this division already has fixtures for its current season."""
        count = self.db.scalar(
            select(func.count())
            .select_from(Match)
            .where(
                Match.divisionId == division.id,
                Match.seasonNumber == division.seasonNumber,
            )
        )
        return bool(count)

    def generate_double_round_robin(self, division: Division) -> list[Match]:
        """Create and persist every fixture for the division's season.

        Teams are ordered by id so the schedule is deterministic. A division
        with fewer than two teams (or an odd count) yields no fixtures.
        """
        team_ids = self._division_team_ids(division.id)
        if len(team_ids) < LEGS or len(team_ids) % 2 != 0:
            return []

        matches = [
            Match(
                divisionId=division.id,
                seasonNumber=division.seasonNumber,
                round=round_number,
                homeTeamId=home_id,
                awayTeamId=away_id,
            )
            for round_number, pairings in enumerate(self._rounds(team_ids), start=1)
            for home_id, away_id in pairings
        ]
        self.db.add_all(matches)
        self.db.commit()
        return matches

    def _division_team_ids(self, division_id: uuid.UUID) -> list[uuid.UUID]:
        return list(
            self.db.scalars(
                select(Team.id)
                .where(Team.divisionId == division_id)
                .order_by(Team.id.asc())
            ).all()
        )

    def _rounds(
        self, team_ids: list[uuid.UUID]
    ) -> list[list[tuple[uuid.UUID, uuid.UUID]]]:
        """Both legs' rounds: the second leg mirrors the first with sides swapped."""
        first_leg = self._single_round_robin(team_ids)
        second_leg = [
            [(away, home) for home, away in pairings] for pairings in first_leg
        ]
        return first_leg + second_leg

    def _single_round_robin(
        self, team_ids: list[uuid.UUID]
    ) -> list[list[tuple[uuid.UUID, uuid.UUID]]]:
        """Circle method: fix the first team, rotate the rest each round."""
        rotation = list(team_ids)
        half = len(rotation) // 2
        rounds: list[list[tuple[uuid.UUID, uuid.UUID]]] = []
        for round_index in range(len(rotation) - 1):
            pairings = [
                self._orient(rotation[i], rotation[-1 - i], round_index)
                for i in range(half)
            ]
            rounds.append(pairings)
            rotation = [rotation[0], rotation[-1], *rotation[1:-1]]
        return rounds

    def _orient(
        self, first: uuid.UUID, second: uuid.UUID, round_index: int
    ) -> tuple[uuid.UUID, uuid.UUID]:
        """Alternate home advantage by round parity so no team is always home."""
        if round_index % 2 == 0:
            return first, second
        return second, first
