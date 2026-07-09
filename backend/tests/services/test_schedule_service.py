from collections import Counter

from sqlalchemy.orm import Session

from app.models.team import Team
from app.services.schedule_service import ScheduleService
from tests.factories import make_division, make_team


def _fill_division(db: Session, division_id, *, count: int = 10) -> list[Team]:
    return [
        make_team(
            db, team_name=f"Team {i}", division_id=division_id
        )
        for i in range(count)
    ]


def test_generates_full_double_round_robin(db_session: Session) -> None:
    division = make_division(db_session)
    _fill_division(db_session, division.id)

    matches = ScheduleService(db_session).generate_double_round_robin(division)

    # 10 teams → 18 rounds of 5 matches = 90 fixtures.
    assert len(matches) == 90
    assert {match.round for match in matches} == set(range(1, 19))
    per_round = Counter(match.round for match in matches)
    assert all(count == 5 for count in per_round.values())


def test_each_team_plays_once_per_round(db_session: Session) -> None:
    division = make_division(db_session)
    teams = _fill_division(db_session, division.id)

    matches = ScheduleService(db_session).generate_double_round_robin(division)

    for round_number in range(1, 19):
        playing = [m for m in matches if m.round == round_number]
        team_ids = [m.homeTeamId for m in playing] + [m.awayTeamId for m in playing]
        assert len(team_ids) == len(set(team_ids)) == len(teams)


def test_every_pair_meets_twice_home_and_away(db_session: Session) -> None:
    division = make_division(db_session)
    _fill_division(db_session, division.id)

    matches = ScheduleService(db_session).generate_double_round_robin(division)

    ordered = Counter((m.homeTeamId, m.awayTeamId) for m in matches)
    # Each ordered (home, away) pairing occurs exactly once...
    assert all(count == 1 for count in ordered.values())
    # ...and its reverse (the away leg) also exists.
    for home_id, away_id in ordered:
        assert (away_id, home_id) in ordered


def test_persists_fixtures_and_reports_has_fixtures(db_session: Session) -> None:
    division = make_division(db_session)
    _fill_division(db_session, division.id)
    service = ScheduleService(db_session)

    assert service.has_fixtures(division) is False
    service.generate_double_round_robin(division)
    assert service.has_fixtures(division) is True


def test_no_fixtures_when_division_too_small(db_session: Session) -> None:
    division = make_division(db_session)
    make_team(db_session, team_name="Lonely", division_id=division.id)

    matches = ScheduleService(db_session).generate_double_round_robin(division)

    assert matches == []
