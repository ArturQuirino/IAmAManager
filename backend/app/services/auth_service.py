import random
from datetime import datetime, timezone

from jose import jwt
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.exceptions import conflict, unauthorized
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.competition_service import CompetitionService
from app.services.player_generator import PlayerGenerator
from app.services.teams_service import TeamsService
from app.services.users_service import PlayersService, UsersService

settings = get_settings()
ALGORITHM = "HS256"


class AuthService:
    def __init__(self, db: Session, *, rng: random.Random | None = None):
        self.db = db
        self._rng = rng or random.Random()
        self.users_service = UsersService(db)
        self.teams_service = TeamsService(db)
        self.players_service = PlayersService(db)
        self.competition_service = CompetitionService(db, rng=self._rng)
        self._generator = PlayerGenerator(self._rng)

    def validate_user(self, email: str, password: str) -> User | None:
        user = self.users_service.find_by_email(email)
        if not user:
            return None

        if not self.users_service.validate_password(password, user.password):
            return None

        return user

    def create_access_token(self, user: User) -> str:
        expire = datetime.now(timezone.utc) + settings.jwt_expires_delta
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "exp": expire,
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)

    def login(self, login_request: LoginRequest) -> TokenResponse:
        user = self.validate_user(login_request.email, login_request.password)
        if not user:
            raise unauthorized("auth.invalidCredentials")

        return TokenResponse(access_token=self.create_access_token(user))

    def register(self, register_request: RegisterRequest) -> TokenResponse:
        """Public sign-up: create the user, their team and squad, place them in
        the bottom division, and return a token so they land already logged in.
        """
        if self.users_service.find_by_email(register_request.email):
            raise conflict("auth.emailAlreadyExists")

        user = self.users_service.create(
            email=register_request.email,
            plain_password=register_request.password,
        )
        team = self.teams_service.create(
            team_name=register_request.teamName, user_id=user.id
        )
        self.players_service.add_generated(team.id, self._generator.random_squad())
        self.competition_service.place_new_team(team)

        return TokenResponse(access_token=self.create_access_token(user))
