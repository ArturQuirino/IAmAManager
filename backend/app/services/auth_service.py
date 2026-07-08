from datetime import datetime, timezone

from jose import jwt
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.exceptions import unauthorized
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.users_service import UsersService

settings = get_settings()
ALGORITHM = "HS256"


class AuthService:
    def __init__(self, db: Session):
        self.users_service = UsersService(db)

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
