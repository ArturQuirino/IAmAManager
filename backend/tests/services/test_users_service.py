import uuid

from sqlalchemy.orm import Session

from app.services.users_service import UsersService
from tests.factories import make_user


def test_create_hashes_password(db_session: Session) -> None:
    service = UsersService(db_session)

    user = service.create(email="a@b.com", plain_password="pw123456")

    assert user.id is not None
    # The plaintext must never be stored; bcrypt hashes start with "$2".
    assert user.password != "pw123456"
    assert user.password.startswith("$2")


def test_validate_password_matches_and_rejects(db_session: Session) -> None:
    service = UsersService(db_session)
    user = service.create(email="a@b.com", plain_password="pw123456")

    assert service.validate_password("pw123456", user.password) is True
    assert service.validate_password("wrong-password", user.password) is False


def test_find_by_email(db_session: Session) -> None:
    service = UsersService(db_session)
    make_user(db_session, email="found@b.com")

    assert service.find_by_email("found@b.com") is not None
    assert service.find_by_email("missing@b.com") is None


def test_find_by_id(db_session: Session) -> None:
    service = UsersService(db_session)
    user = make_user(db_session, email="id@b.com")

    assert service.find_by_id(user.id).email == "id@b.com"
    assert service.find_by_id(uuid.uuid4()) is None
