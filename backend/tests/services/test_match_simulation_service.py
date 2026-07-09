import random

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.player import PlayerPosition
from app.services.match_simulation_service import (
    ATTACKING_WEIGHTS,
    MATCH_MINUTES,
    MatchSimulationService,
    attacker_wins,
    defender_wins,
)
from tests.factories import (
    make_division,
    make_match,
    make_player,
    make_starting_xi,
    make_team,
)


def _service(db: Session, seed: int = 7) -> MatchSimulationService:
    return MatchSimulationService(db, rng=random.Random(seed))


def _fixture(db: Session):
    """A division with two fully lined-up teams and a match between them."""
    division = make_division(db)
    home = make_team(db, team_name="Home FC", division_id=division.id)
    away = make_team(db, team_name="Away FC", division_id=division.id)
    make_starting_xi(db, home.id, prefix="H")
    make_starting_xi(db, away.id, prefix="A")
    match = make_match(
        db, division_id=division.id, home_team_id=home.id, away_team_id=away.id
    )
    return home, away, match


# --- Pure tie-break helpers ---------------------------------------------------


def test_attacker_loses_on_exact_tie() -> None:
    # roll == max_roll - chance is not a strict exceed → failure (defence wins).
    assert attacker_wins(roll=110, chance=40, max_roll=150) is False
    assert attacker_wins(roll=111, chance=40, max_roll=150) is True


def test_defender_wins_on_exact_tie() -> None:
    # For defensive stages a tie counts as success (defence wins).
    assert defender_wins(roll=110, chance=40, max_roll=150) is True
    assert defender_wins(roll=109, chance=40, max_roll=150) is False


# --- Engine invariants --------------------------------------------------------


def test_simulate_marks_played_with_a_full_event_log(db_session: Session) -> None:
    _, _, match = _fixture(db_session)

    _service(db_session).simulate(match)

    assert match.played is True
    assert match.homeScore is not None and match.awayScore is not None
    # One play per minute from 0 to 90 inclusive.
    assert len(match.eventLog) == MATCH_MINUTES
    assert [event["minute"] for event in match.eventLog] == list(range(MATCH_MINUTES))


def test_score_equals_the_number_of_goal_events(db_session: Session) -> None:
    _, _, match = _fixture(db_session)

    _service(db_session).simulate(match)

    home_goals = sum(
        1 for e in match.eventLog if e["outcome"] == "goal" and e["isHome"]
    )
    away_goals = sum(
        1 for e in match.eventLog if e["outcome"] == "goal" and not e["isHome"]
    )
    assert match.homeScore == home_goals
    assert match.awayScore == away_goals
    # The running score on the last event matches the final score.
    assert match.eventLog[-1]["homeScore"] == match.homeScore
    assert match.eventLog[-1]["awayScore"] == match.awayScore


def test_only_starters_appear_in_the_event_log(db_session: Session) -> None:
    home, away, match = _fixture(db_session)
    # Add a benched player to each side; it must never take part.
    make_player(db_session, home.id, name="H-BENCH", position=PlayerPosition.ATT)
    make_player(db_session, away.id, name="A-BENCH", position=PlayerPosition.ATT)

    _service(db_session).simulate(match)

    named = {event["player"] for event in match.eventLog}
    assert "H-BENCH" not in named
    assert "A-BENCH" not in named


def test_standings_updated_for_both_teams(db_session: Session) -> None:
    home, away, match = _fixture(db_session)

    _service(db_session).simulate(match)

    assert home.played == 1
    assert away.played == 1
    assert home.goalsFor == match.homeScore == away.goalsAgainst
    assert away.goalsFor == match.awayScore == home.goalsAgainst
    if match.homeScore > match.awayScore:
        assert home.points == 3 and away.points == 0
        assert home.wins == 1 and away.losses == 1
    elif match.homeScore < match.awayScore:
        assert away.points == 3 and home.points == 0
    else:
        assert home.points == 1 and away.points == 1
        assert home.draws == 1 and away.draws == 1


def test_simulation_is_deterministic_for_a_fixed_seed(db_session: Session) -> None:
    division = make_division(db_session)
    home = make_team(db_session, team_name="Home", division_id=division.id)
    away = make_team(db_session, team_name="Away", division_id=division.id)
    make_starting_xi(db_session, home.id, prefix="H")
    make_starting_xi(db_session, away.id, prefix="A")
    first = make_match(
        db_session, division_id=division.id, home_team_id=home.id, away_team_id=away.id
    )
    second = make_match(
        db_session,
        division_id=division.id,
        home_team_id=home.id,
        away_team_id=away.id,
        round_number=2,
    )

    MatchSimulationService(db_session, rng=random.Random(99)).simulate(first)
    MatchSimulationService(db_session, rng=random.Random(99)).simulate(second)

    assert (first.homeScore, first.awayScore) == (second.homeScore, second.awayScore)
    assert first.eventLog == second.eventLog


def test_shooter_is_never_the_passer(db_session: Session) -> None:
    home = make_team(db_session, team_name="Home")
    starters = make_starting_xi(db_session, home.id, prefix="H")
    service = _service(db_session)
    passer = starters[1]  # a defender, present in the pool

    for _ in range(200):
        shooter = service._pick(starters, ATTACKING_WEIGHTS, exclude=passer)
        assert shooter is not passer


def test_rejects_an_incomplete_lineup(db_session: Session) -> None:
    division = make_division(db_session)
    home = make_team(db_session, team_name="Home", division_id=division.id)
    away = make_team(db_session, team_name="Away", division_id=division.id)
    make_starting_xi(db_session, home.id, prefix="H")
    # Away side only has ten starters (missing a player).
    for index in range(10):
        make_player(
            db_session, away.id, name=f"A{index}",
            position=PlayerPosition.DEF, is_starter=True,
        )
    match = make_match(
        db_session, division_id=division.id, home_team_id=home.id, away_team_id=away.id
    )

    with pytest.raises(HTTPException) as exc:
        _service(db_session).simulate(match)

    assert exc.value.status_code == 422
    assert exc.value.detail["errorCode"] == "match.lineupIncomplete"
