from sqlalchemy.orm import Session

from app.models.player import PlayerPosition
from app.services.users_service import PlayersService
from tests.factories import make_player, make_user


def test_create_maps_keyword_fields(db_session: Session) -> None:
    user = make_user(db_session)

    player = make_player(
        db_session,
        user.id,
        name="Zico",
        position=PlayerPosition.CAM,
        shirt_number=10,
    )

    assert player.id is not None
    assert player.name == "Zico"
    assert player.shirtNumber == 10
    assert player.userId == user.id


def test_count_by_user_id(db_session: Session) -> None:
    service = PlayersService(db_session)
    user = make_user(db_session)

    assert service.count_by_user_id(user.id) == 0
    make_player(db_session, user.id)
    assert service.count_by_user_id(user.id) == 1


def test_find_by_user_id_isolates_owners(db_session: Session) -> None:
    owner = make_user(db_session, email="owner@b.com")
    other = make_user(db_session, email="other@b.com")
    make_player(db_session, owner.id, name="Mine")
    make_player(db_session, other.id, name="Theirs")

    names = [p.name for p in PlayersService(db_session).find_by_user_id(owner.id)]

    assert names == ["Mine"]
