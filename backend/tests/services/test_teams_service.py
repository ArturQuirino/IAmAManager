import uuid

from sqlalchemy.orm import Session

from app.services.teams_service import TeamsService
from tests.factories import make_user


def test_create_for_owner(db_session: Session) -> None:
    user = make_user(db_session)
    service = TeamsService(db_session)

    team = service.create(team_name="Owner FC", user_id=user.id)

    assert team.id is not None
    assert team.teamName == "Owner FC"
    assert team.userId == user.id
    assert team.divisionId is None


def test_create_fake_team_has_no_owner(db_session: Session) -> None:
    service = TeamsService(db_session)

    team = service.create(team_name="CPU FC")

    assert team.userId is None


def test_find_by_user_id(db_session: Session) -> None:
    user = make_user(db_session, email="a@b.com")
    other = make_user(db_session, email="b@b.com")
    service = TeamsService(db_session)
    service.create(team_name="Mine", user_id=user.id)

    found = service.find_by_user_id(user.id)

    assert found is not None
    assert found.teamName == "Mine"
    assert service.find_by_user_id(other.id) is None
    assert service.find_by_user_id(uuid.uuid4()) is None
