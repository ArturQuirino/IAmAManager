import random
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.division import Division
from app.models.team import Team
from app.services.player_generator import PlayerGenerator

# Every division holds exactly this many teams (see docs/competition.md).
DIVISION_SIZE = 10
INITIAL_SEASON_NUMBER = 1
# Fake teams are deliberately weak placeholders; a low skill scale keeps their
# generated squads uncompetitive against real, user-owned teams.
FAKE_TEAM_SKILL_SCALE = 0.4

FAKE_TEAM_ADJECTIVES = (
    "Old",
    "North",
    "Royal",
    "United",
    "Athletic",
    "Sporting",
    "Real",
    "Riverside",
    "Central",
    "Wandering",
)
FAKE_TEAM_NOUNS = (
    "Rovers",
    "Wanderers",
    "City",
    "Rangers",
    "Albion",
    "Athletic",
    "Town",
    "County",
    "Harriers",
    "Casuals",
)


class CompetitionService:
    """Divisions, fake (CPU) teams and season standings.

    Match simulation and promotion/relegation are later stages; this service
    only builds the division structure and reads the current table.
    """

    def __init__(self, db: Session, *, rng: random.Random | None = None):
        self.db = db
        self._rng = rng or random.Random()
        self._generator = PlayerGenerator(self._rng)

    def get_lowest_division(self) -> Division | None:
        """The bottom of the pyramid — the division with the highest level."""
        return self.db.scalar(
            select(Division).order_by(Division.level.desc()).limit(1)
        )

    def get_division(self, division_id: uuid.UUID) -> Division | None:
        return self.db.get(Division, division_id)

    def create_division(
        self, *, level: int, season_number: int = INITIAL_SEASON_NUMBER
    ) -> Division:
        division = Division(level=level, seasonNumber=season_number)
        self.db.add(division)
        self.db.commit()
        self.db.refresh(division)
        return division

    def count_teams_in_division(self, division_id: uuid.UUID) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(Team)
                .where(Team.divisionId == division_id)
            )
            or 0
        )

    def create_fake_team(self, division: Division) -> Team:
        """A CPU-owned (userId=None) placeholder with a deliberately weak squad."""
        squad = self._generator.random_squad(skill_scale=FAKE_TEAM_SKILL_SCALE)
        team = Team(
            teamName=self._fake_team_name(),
            userId=None,
            divisionId=division.id,
            players=squad,
        )
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def fill_division_with_fakes(self, division: Division) -> list[Team]:
        """Top the division up to DIVISION_SIZE with fresh fake teams."""
        missing = DIVISION_SIZE - self.count_teams_in_division(division.id)
        return [self.create_fake_team(division) for _ in range(max(0, missing))]

    def get_division_standings(self, division_id: uuid.UUID) -> list[Team]:
        """Teams in the division ranked by points, then goal difference.

        Goals scored, team name and id are stable, deterministic further
        tie-breaks so the ordering is fully defined (and reproducible across
        queries) even when points and GD are level.
        """
        goal_difference = Team.goalsFor - Team.goalsAgainst
        return list(
            self.db.scalars(
                select(Team)
                .where(Team.divisionId == division_id)
                .order_by(
                    Team.points.desc(),
                    goal_difference.desc(),
                    Team.goalsFor.desc(),
                    Team.teamName.asc(),
                    Team.id.asc(),
                )
            ).all()
        )

    def _fake_team_name(self) -> str:
        return (
            f"{self._rng.choice(FAKE_TEAM_ADJECTIVES)} "
            f"{self._rng.choice(FAKE_TEAM_NOUNS)}"
        )
