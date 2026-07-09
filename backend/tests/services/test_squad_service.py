import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.player import PlayerPosition
from app.services.squad_service import SquadService
from tests.factories import (
    make_player,
    make_squad,
    make_team,
    make_user_with_team,
)


def error_code(exc: HTTPException) -> str:
    assert isinstance(exc.detail, dict)
    return exc.detail["errorCode"]


def test_get_squad_groups_by_position(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    make_player(db_session, team.id, name="Striker", position=PlayerPosition.ATT)
    make_player(db_session, team.id, name="Keeper", position=PlayerPosition.GK)
    make_player(db_session, team.id, name="Back", position=PlayerPosition.DEF)

    squad = SquadService(db_session).get_squad(team)

    assert [player.position for player in squad] == [
        PlayerPosition.GK,
        PlayerPosition.DEF,
        PlayerPosition.ATT,
    ]


def test_remove_outfield_player_succeeds_above_minimum(
    db_session: Session,
) -> None:
    _, team = make_user_with_team(db_session)
    make_squad(db_session, team.id, goalkeepers=1, outfield=11)
    target = SquadService(db_session).get_squad(team)[-1]

    SquadService(db_session).remove_player(team, target.id)

    remaining = SquadService(db_session).get_squad(team)
    assert target.id not in {player.id for player in remaining}
    assert len(remaining) == 11


def test_remove_goalkeeper_succeeds_with_a_spare(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    make_squad(db_session, team.id, goalkeepers=2, outfield=10)
    keeper = next(
        player
        for player in SquadService(db_session).get_squad(team)
        if player.position == PlayerPosition.GK
    )

    SquadService(db_session).remove_player(team, keeper.id)

    survivors = SquadService(db_session).get_squad(team)
    goalkeepers = [p for p in survivors if p.position == PlayerPosition.GK]
    assert len(goalkeepers) == 1


def test_remove_last_goalkeeper_is_rejected(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    make_squad(db_session, team.id, goalkeepers=1, outfield=10)
    keeper = SquadService(db_session).get_squad(team)[0]

    with pytest.raises(HTTPException) as exc:
        SquadService(db_session).remove_player(team, keeper.id)

    assert exc.value.status_code == 409
    assert error_code(exc.value) == "squad.minGoalkeeper"
    assert len(SquadService(db_session).get_squad(team)) == 11


def test_remove_outfield_at_minimum_is_rejected(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    make_squad(db_session, team.id, goalkeepers=1, outfield=10)
    outfielder = SquadService(db_session).get_squad(team)[-1]

    with pytest.raises(HTTPException) as exc:
        SquadService(db_session).remove_player(team, outfielder.id)

    assert exc.value.status_code == 409
    assert error_code(exc.value) == "squad.minOutfield"


def test_remove_missing_player_is_not_found(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    make_squad(db_session, team.id)

    with pytest.raises(HTTPException) as exc:
        SquadService(db_session).remove_player(team, uuid.uuid4())

    assert exc.value.status_code == 404
    assert error_code(exc.value) == "squad.playerNotFound"


def test_cannot_remove_another_teams_player(db_session: Session) -> None:
    _, team = make_user_with_team(db_session, email="owner@b.com")
    other = make_team(db_session, team_name="Other FC")
    make_squad(db_session, team.id)
    intruder = make_player(db_session, other.id, name="Theirs")

    with pytest.raises(HTTPException) as exc:
        SquadService(db_session).remove_player(team, intruder.id)

    assert exc.value.status_code == 404
    assert error_code(exc.value) == "squad.playerNotFound"
