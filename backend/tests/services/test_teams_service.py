import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.teams_service import TeamsService
from tests.factories import make_team, make_user, make_user_with_team


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


def test_find_by_name_is_case_insensitive(db_session: Session) -> None:
    service = TeamsService(db_session)
    service.create(team_name="Real Madrid")

    assert service.find_by_name("real madrid") is not None
    assert service.find_by_name("REAL MADRID") is not None
    assert service.find_by_name("Barcelona") is None


def test_find_by_name_can_exclude_a_team(db_session: Session) -> None:
    service = TeamsService(db_session)
    team = service.create(team_name="Only One")

    assert service.find_by_name("Only One", exclude_team_id=team.id) is None


def test_rename_updates_the_team_name(db_session: Session) -> None:
    _, team = make_user_with_team(db_session, team_name="Old Name")
    service = TeamsService(db_session)

    renamed = service.rename(team, "New Name")

    assert renamed.teamName == "New Name"
    assert service.find_by_user_id(team.userId).teamName == "New Name"


def test_rename_to_same_name_is_allowed(db_session: Session) -> None:
    _, team = make_user_with_team(db_session, team_name="Keep Me")
    service = TeamsService(db_session)

    renamed = service.rename(team, "Keep Me")

    assert renamed.teamName == "Keep Me"


def test_rename_rejects_a_name_taken_by_another_team(db_session: Session) -> None:
    make_team(db_session, team_name="Taken FC")
    _, team = make_user_with_team(db_session, team_name="Mine FC")
    service = TeamsService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.rename(team, "taken fc")

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["errorCode"] == "team.nameAlreadyExists"
