import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.player import Player, PlayerPosition
from app.services.tactics_service import (
    TacticsService,
    derive_formation,
)
from tests.factories import make_player, make_user_with_team


def error_code(exc: HTTPException) -> str:
    assert isinstance(exc.detail, dict)
    return exc.detail["errorCode"]


def _valid_xi(db: Session, team_id: uuid.UUID) -> list[Player]:
    """One goalkeeper plus ten outfield players (4 DEF, 3 MID, 3 ATT)."""
    players = [make_player(db, team_id, name="GK", position=PlayerPosition.GK)]
    lines = (
        [PlayerPosition.DEF] * 4
        + [PlayerPosition.MID] * 3
        + [PlayerPosition.ATT] * 3
    )
    for index, position in enumerate(lines):
        players.append(
            make_player(db, team_id, name=f"P{index}", position=position)
        )
    return players


def test_set_starting_xi_marks_exactly_those_players(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    xi = _valid_xi(db_session, team.id)
    bench_player = make_player(
        db_session, team.id, name="Bench", position=PlayerPosition.MID
    )

    starters, bench = TacticsService(db_session).set_starting_xi(
        team, [player.id for player in xi]
    )

    assert {player.id for player in starters} == {player.id for player in xi}
    assert [player.id for player in bench] == [bench_player.id]


def test_set_starting_xi_replaces_previous_selection(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    xi = _valid_xi(db_session, team.id)
    spare = make_player(
        db_session, team.id, name="Spare", position=PlayerPosition.DEF
    )
    service = TacticsService(db_session)
    service.set_starting_xi(team, [player.id for player in xi])

    # Swap one defender (xi[1]) out for the spare defender, keeping the keeper.
    new_ids = [xi[0].id] + [player.id for player in xi[2:]] + [spare.id]
    starters, _ = service.set_starting_xi(team, new_ids)

    assert xi[1].id not in {player.id for player in starters}
    assert spare.id in {player.id for player in starters}
    assert sum(player.isStarter for player in service._team_players(team)) == 11


def test_set_starting_xi_rejects_wrong_count(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    xi = _valid_xi(db_session, team.id)

    with pytest.raises(HTTPException) as exc:
        TacticsService(db_session).set_starting_xi(
            team, [player.id for player in xi[:10]]
        )

    assert exc.value.status_code == 422
    assert error_code(exc.value) == "tactics.mustBe11"


def test_set_starting_xi_rejects_duplicate_ids(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    xi = _valid_xi(db_session, team.id)
    ids = [player.id for player in xi[:10]] + [xi[0].id]  # 11 ids, one repeated

    with pytest.raises(HTTPException) as exc:
        TacticsService(db_session).set_starting_xi(team, ids)

    assert exc.value.status_code == 422
    assert error_code(exc.value) == "tactics.mustBe11"


def test_set_starting_xi_rejects_zero_goalkeepers(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    outfield = [
        make_player(db_session, team.id, name=f"O{i}", position=PlayerPosition.MID)
        for i in range(11)
    ]

    with pytest.raises(HTTPException) as exc:
        TacticsService(db_session).set_starting_xi(
            team, [player.id for player in outfield]
        )

    assert exc.value.status_code == 422
    assert error_code(exc.value) == "tactics.needExactlyOneGk"


def test_set_starting_xi_rejects_two_goalkeepers(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    keepers = [
        make_player(db_session, team.id, name=f"GK{i}", position=PlayerPosition.GK)
        for i in range(2)
    ]
    outfield = [
        make_player(db_session, team.id, name=f"O{i}", position=PlayerPosition.DEF)
        for i in range(9)
    ]

    with pytest.raises(HTTPException) as exc:
        TacticsService(db_session).set_starting_xi(
            team, [player.id for player in keepers + outfield]
        )

    assert exc.value.status_code == 422
    assert error_code(exc.value) == "tactics.needExactlyOneGk"


def test_set_starting_xi_rejects_another_teams_player(db_session: Session) -> None:
    _, team = make_user_with_team(db_session, email="owner@b.com")
    _, other = make_user_with_team(db_session, email="other@b.com")
    xi = _valid_xi(db_session, team.id)
    intruder = make_player(db_session, other.id, name="Theirs")
    ids = [player.id for player in xi[:10]] + [intruder.id]

    with pytest.raises(HTTPException) as exc:
        TacticsService(db_session).set_starting_xi(team, ids)

    assert exc.value.status_code == 404
    assert error_code(exc.value) == "tactics.playerNotFound"
    # Nothing was persisted: the intruder never joined, no starter was marked.
    assert all(not p.isStarter for p in TacticsService(db_session)._team_players(team))


def test_get_tactics_splits_starters_and_bench(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    xi = _valid_xi(db_session, team.id)
    make_player(db_session, team.id, name="Reserve", position=PlayerPosition.ATT)
    service = TacticsService(db_session)
    service.set_starting_xi(team, [player.id for player in xi])

    starters, bench = service.get_tactics(team)

    assert len(starters) == 11
    assert [player.name for player in bench] == ["Reserve"]
    # Both lists are grouped by position, goalkeeper first.
    assert starters[0].position == PlayerPosition.GK


def test_derive_formation_reads_outfield_shape() -> None:
    starters = [Player(name="GK", position=PlayerPosition.GK)]
    starters += [Player(name=f"D{i}", position=PlayerPosition.DEF) for i in range(4)]
    starters += [Player(name=f"M{i}", position=PlayerPosition.MID) for i in range(3)]
    starters += [Player(name=f"A{i}", position=PlayerPosition.ATT) for i in range(3)]

    assert derive_formation(starters) == "4-3-3"


def test_derive_formation_handles_other_shapes() -> None:
    starters = [Player(name="GK", position=PlayerPosition.GK)]
    starters += [Player(name=f"D{i}", position=PlayerPosition.DEF) for i in range(5)]
    starters += [Player(name=f"M{i}", position=PlayerPosition.MID) for i in range(4)]
    starters += [Player(name="A0", position=PlayerPosition.ATT)]

    assert derive_formation(starters) == "5-4-1"


def test_derive_formation_is_none_without_starters() -> None:
    assert derive_formation([]) is None
