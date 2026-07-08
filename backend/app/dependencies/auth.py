import uuid
from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.database.session import get_db
from app.exceptions import unauthorized
from app.services.users_service import UsersService

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
ALGORITHM = "HS256"


@dataclass
class CurrentUser:
    user_id: uuid.UUID
    email: str


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if token is None:
        raise unauthorized("Credenciais inválidas")

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id is None or email is None:
            raise unauthorized("Credenciais inválidas")
    except JWTError:
        raise unauthorized("Credenciais inválidas") from None

    users_service = UsersService(db)
    user = users_service.find_by_id(uuid.UUID(user_id))
    if not user:
        raise unauthorized("Credenciais inválidas")

    return CurrentUser(user_id=user.id, email=user.email)
