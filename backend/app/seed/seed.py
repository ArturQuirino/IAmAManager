import logging

from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.player import PlayerPosition
from app.services.users_service import PlayersService, UsersService

logger = logging.getLogger(__name__)

TEST_USER_EMAIL = "admin@fm.local"
TEST_USER_PASSWORD = "admin123"
TEST_TEAM_NAME = "FC Cursor"

SEED_PLAYERS = [
    {"name": "Marco Silva", "position": PlayerPosition.GK, "shirt_number": 1, "age": 28, "nationality": "Portugal", "overall": 82},
    {"name": "Lucas Fernandez", "position": PlayerPosition.GK, "shirt_number": 13, "age": 24, "nationality": "Argentina", "overall": 74},
    {"name": "Henrik Dahl", "position": PlayerPosition.GK, "shirt_number": 25, "age": 19, "nationality": "Denmark", "overall": 65},
    {"name": "James Whitmore", "position": PlayerPosition.RB, "shirt_number": 2, "age": 26, "nationality": "England", "overall": 79},
    {"name": "Diego Morales", "position": PlayerPosition.RB, "shirt_number": 22, "age": 21, "nationality": "Spain", "overall": 72},
    {"name": "Antoine Dubois", "position": PlayerPosition.LB, "shirt_number": 3, "age": 27, "nationality": "France", "overall": 80},
    {"name": "Erik Lindqvist", "position": PlayerPosition.LB, "shirt_number": 15, "age": 23, "nationality": "Sweden", "overall": 75},
    {"name": "Carlos Mendes", "position": PlayerPosition.CB, "shirt_number": 4, "age": 30, "nationality": "Brazil", "overall": 83},
    {"name": "Nikolai Petrov", "position": PlayerPosition.CB, "shirt_number": 5, "age": 29, "nationality": "Russia", "overall": 81},
    {"name": "Kwame Osei", "position": PlayerPosition.CB, "shirt_number": 6, "age": 25, "nationality": "Ghana", "overall": 77},
    {"name": "Matteo Rossi", "position": PlayerPosition.CB, "shirt_number": 24, "age": 20, "nationality": "Italy", "overall": 70},
    {"name": "Thomas Becker", "position": PlayerPosition.CDM, "shirt_number": 8, "age": 28, "nationality": "Germany", "overall": 82},
    {"name": "Yuki Tanaka", "position": PlayerPosition.CDM, "shirt_number": 14, "age": 26, "nationality": "Japan", "overall": 78},
    {"name": "Andreas Christou", "position": PlayerPosition.CM, "shirt_number": 10, "age": 27, "nationality": "Greece", "overall": 84},
    {"name": "Felipe Costa", "position": PlayerPosition.CM, "shirt_number": 16, "age": 24, "nationality": "Brazil", "overall": 76},
    {"name": "Oliver Hughes", "position": PlayerPosition.CM, "shirt_number": 18, "age": 22, "nationality": "Wales", "overall": 73},
    {"name": "Rafael Santos", "position": PlayerPosition.CAM, "shirt_number": 7, "age": 25, "nationality": "Portugal", "overall": 85},
    {"name": "Ibrahim Al-Hassan", "position": PlayerPosition.CAM, "shirt_number": 20, "age": 23, "nationality": "Morocco", "overall": 77},
    {"name": "Lucas Berg", "position": PlayerPosition.LW, "shirt_number": 11, "age": 26, "nationality": "Netherlands", "overall": 83},
    {"name": "Samuel Okonkwo", "position": PlayerPosition.LW, "shirt_number": 17, "age": 21, "nationality": "Nigeria", "overall": 74},
    {"name": "Victor Andersson", "position": PlayerPosition.RW, "shirt_number": 9, "age": 28, "nationality": "Sweden", "overall": 86},
    {"name": "Mateo Garcia", "position": PlayerPosition.RW, "shirt_number": 19, "age": 22, "nationality": "Colombia", "overall": 75},
    {"name": "Stefan Novak", "position": PlayerPosition.ST, "shirt_number": 12, "age": 29, "nationality": "Croatia", "overall": 87},
    {"name": "Emmanuel Koffi", "position": PlayerPosition.ST, "shirt_number": 21, "age": 24, "nationality": "Ivory Coast", "overall": 79},
    {"name": "Pierre Martin", "position": PlayerPosition.ST, "shirt_number": 23, "age": 19, "nationality": "France", "overall": 68},
    {"name": "David Kowalski", "position": PlayerPosition.ST, "shirt_number": 27, "age": 32, "nationality": "Poland", "overall": 80},
]


def run_seed(db: Session) -> None:
    settings = get_settings()
    if not settings.should_seed:
        logger.info("Seed skipped (RUN_SEED not enabled)")
        return

    logger.info("Running database seed...")

    users_service = UsersService(db)
    players_service = PlayersService(db)

    user = users_service.find_by_email(TEST_USER_EMAIL)
    if not user:
        user = users_service.create(TEST_USER_EMAIL, TEST_USER_PASSWORD, TEST_TEAM_NAME)
        logger.info("Created test user: %s", TEST_USER_EMAIL)
    else:
        logger.info("Test user already exists: %s", TEST_USER_EMAIL)

    existing_count = players_service.count_by_user_id(user.id)
    if existing_count > 0:
        logger.info("Players already seeded (%s players)", existing_count)
        return

    for player_data in SEED_PLAYERS:
        players_service.create(user_id=user.id, **player_data)

    logger.info("Seeded %s players for %s", len(SEED_PLAYERS), TEST_TEAM_NAME)
