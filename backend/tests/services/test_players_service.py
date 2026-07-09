from sqlalchemy.orm import Session

from app.models.player import PlayerPosition
from app.services.users_service import PlayersService
from tests.factories import make_player, make_team


def test_create_maps_keyword_fields(db_session: Session) -> None:
    team = make_team(db_session)

    player = make_player(
        db_session,
        team.id,
        name="Zico",
        position=PlayerPosition.MID,
        passing=88,
    )

    assert player.id is not None
    assert player.name == "Zico"
    assert player.position == PlayerPosition.MID
    assert player.passing == 88
    assert player.teamId == team.id


def test_overall_is_derived_from_attributes(db_session: Session) -> None:
    team = make_team(db_session)

    player = make_player(
        db_session,
        team.id,
        pace=80,
        shooting=80,
        passing=80,
        dribbling=80,
        defending=80,
        physical=80,
    )

    assert player.overall == 80


def test_overall_rounds_half_up(db_session: Session) -> None:
    team = make_team(db_session)

    # Sum 3 → average 0.5 → rounds up to 1 (not banker's-rounded to 0).
    player = make_player(
        db_session,
        team.id,
        pace=1,
        shooting=1,
        passing=1,
        dribbling=0,
        defending=0,
        physical=0,
    )

    assert player.overall == 1


def test_count_by_team_id(db_session: Session) -> None:
    service = PlayersService(db_session)
    team = make_team(db_session)

    assert service.count_by_team_id(team.id) == 0
    make_player(db_session, team.id)
    assert service.count_by_team_id(team.id) == 1


def test_find_by_team_id_isolates_teams(db_session: Session) -> None:
    owner = make_team(db_session, team_name="Owner FC")
    other = make_team(db_session, team_name="Other FC")
    make_player(db_session, owner.id, name="Mine")
    make_player(db_session, other.id, name="Theirs")

    names = [p.name for p in PlayersService(db_session).find_by_team_id(owner.id)]

    assert names == ["Mine"]
