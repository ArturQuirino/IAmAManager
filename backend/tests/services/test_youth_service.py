import random
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.player import PlayerPosition
from app.services.squad_service import MAX_SQUAD_SIZE
from app.services.youth_service import YOUTH_POSITIONS, YouthService
from tests.factories import make_player, make_team, make_user_with_team


def seeded_service(db: Session, seed: int = 1) -> YouthService:
    return YouthService(db, rng=random.Random(seed))


def error_code(exc: HTTPException) -> str:
    assert isinstance(exc.detail, dict)
    return exc.detail["errorCode"]


def test_get_current_generates_one_candidate_per_position(
    db_session: Session,
) -> None:
    _, team = make_user_with_team(db_session)

    candidates = seeded_service(db_session).get_current(team)

    assert len(candidates) == len(YOUTH_POSITIONS)
    assert {candidate.position for candidate in candidates} == set(
        YOUTH_POSITIONS
    )


def test_get_current_is_stable_across_calls(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    service = seeded_service(db_session)

    first = {candidate.id for candidate in service.get_current(team)}
    second = {candidate.id for candidate in service.get_current(team)}

    assert first == second


def test_refresh_week_replaces_the_batch(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    service = seeded_service(db_session)
    original = {candidate.id for candidate in service.get_current(team)}

    refreshed = service.refresh_week(team)

    assert len(refreshed) == len(YOUTH_POSITIONS)
    assert {candidate.id for candidate in refreshed}.isdisjoint(original)
    current = {candidate.id for candidate in service.get_current(team)}
    assert current.isdisjoint(original)


def test_add_to_squad_promotes_candidate(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    service = seeded_service(db_session)
    candidate = service.get_current(team)[0]

    player = service.add_to_squad(team, candidate.id)

    assert player.teamId == team.id
    assert player.position == candidate.position
    assert player.overall == candidate.overall
    assert player.isStarter is False
    # The promoted candidate is gone; the rest of the week remains.
    assert len(service.get_current(team)) == len(YOUTH_POSITIONS) - 1


def test_add_to_squad_rejects_when_squad_is_full(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)
    for index in range(MAX_SQUAD_SIZE):
        make_player(db_session, team.id, name=f"P{index}")
    service = seeded_service(db_session)
    candidate = service.get_current(team)[0]

    with pytest.raises(HTTPException) as exc:
        service.add_to_squad(team, candidate.id)

    assert exc.value.status_code == 409
    assert error_code(exc.value) == "squad.full"
    # The candidate must survive a rejected promotion.
    assert candidate.id in {c.id for c in service.get_current(team)}


def test_add_to_squad_rejects_unknown_candidate(db_session: Session) -> None:
    _, team = make_user_with_team(db_session)

    with pytest.raises(HTTPException) as exc:
        seeded_service(db_session).add_to_squad(team, uuid.uuid4())

    assert exc.value.status_code == 404
    assert error_code(exc.value) == "youth.candidateNotFound"


def test_cannot_add_another_teams_candidate(db_session: Session) -> None:
    _, team = make_user_with_team(db_session, email="owner@b.com")
    other = make_team(db_session, team_name="Other FC")
    others_candidate = seeded_service(db_session).get_current(other)[0]

    with pytest.raises(HTTPException) as exc:
        seeded_service(db_session).add_to_squad(team, others_candidate.id)

    assert exc.value.status_code == 404
    assert error_code(exc.value) == "youth.candidateNotFound"
