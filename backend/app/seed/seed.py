import logging

from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.division import TOP_DIVISION_LEVEL, Division
from app.models.team import Team
from app.services.competition_service import CompetitionService
from app.services.player_generator import PlayerGenerator
from app.services.schedule_service import ScheduleService
from app.services.teams_service import TeamsService
from app.services.users_service import PlayersService, UsersService

logger = logging.getLogger(__name__)

TEST_USER_EMAIL = "admin@fm.local"
TEST_USER_PASSWORD = "admin123"
TEST_TEAM_NAME = "FC Cursor"


def run_seed(db: Session) -> None:
    settings = get_settings()
    if not settings.should_seed:
        logger.info("Seed skipped (RUN_SEED not enabled)")
        return

    logger.info("Running database seed...")

    users_service = UsersService(db)
    teams_service = TeamsService(db)
    players_service = PlayersService(db)

    user = users_service.find_by_email(TEST_USER_EMAIL)
    if not user:
        user = users_service.create(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        logger.info("Created test user: %s", TEST_USER_EMAIL)
    else:
        logger.info("Test user already exists: %s", TEST_USER_EMAIL)

    team = teams_service.find_by_user_id(user.id)
    if not team:
        team = teams_service.create(team_name=TEST_TEAM_NAME, user_id=user.id)
        logger.info("Created team for %s", TEST_USER_EMAIL)

    _ensure_team_in_division(db, team)

    if players_service.count_by_team_id(team.id) == 0:
        squad = PlayerGenerator().random_squad()
        players_service.add_generated(team.id, squad)
        logger.info("Seeded %s players for %s", len(squad), TEST_TEAM_NAME)
    else:
        logger.info("Squad already seeded for %s", TEST_TEAM_NAME)

    if team.divisionId is not None:
        division = db.get(Division, team.divisionId)
        if division is not None:
            _ensure_fixtures(db, division)


def _ensure_team_in_division(db: Session, team: Team) -> None:
    """Place the seed team in the lowest division, filling it with fake teams.

    Idempotent: once the team has a division, later seed runs leave it alone.
    """
    if team.divisionId is not None:
        return

    competition = CompetitionService(db)
    division = competition.get_lowest_division() or competition.create_division(
        level=TOP_DIVISION_LEVEL
    )
    team.divisionId = division.id
    db.commit()
    competition.fill_division_with_fakes(division)
    logger.info("Placed %s in division level %s", team.teamName, division.level)


def _ensure_fixtures(db: Session, division: Division) -> None:
    """Generate the season's fixtures once the division is full.

    Idempotent: a division that already has fixtures for its current season is
    left untouched, so repeated seed runs never duplicate the schedule.
    """
    schedule = ScheduleService(db)
    if schedule.has_fixtures(division):
        return
    matches = schedule.generate_double_round_robin(division)
    if matches:
        logger.info(
            "Generated %s fixtures for division level %s",
            len(matches),
            division.level,
        )
