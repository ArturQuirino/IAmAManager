import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.division import Division
from app.models.match import Match
from app.models.team import Team
from app.services.schedule_service import ScheduleService
from app.services.season_service import SeasonService
from tests.factories import make_division, make_match, make_starting_xi, make_team


def _standing_team(
    db: Session, *, division_id: uuid.UUID, name: str, points: int
) -> Team:
    """A team placed in a division with a controlled points total and record."""
    team = make_team(db, team_name=name, division_id=division_id)
    team.points = points
    team.played = 5
    team.wins = points // 3
    team.goalsFor = points
    team.goalsAgainst = 5
    db.commit()
    return team


def test_is_division_complete_reflects_unplayed_fixtures(
    db_session: Session,
) -> None:
    service = SeasonService(db_session)
    division = make_division(db_session)
    home = make_team(db_session, team_name="A", division_id=division.id)
    away = make_team(db_session, team_name="B", division_id=division.id)
    match = make_match(
        db_session,
        division_id=division.id,
        home_team_id=home.id,
        away_team_id=away.id,
    )

    assert service.is_division_complete(division) is False

    match.played = True
    db_session.commit()
    assert service.is_division_complete(division) is True


def test_is_division_complete_false_without_fixtures(db_session: Session) -> None:
    division = make_division(db_session)

    assert SeasonService(db_session).is_division_complete(division) is False


def test_is_pyramid_complete_requires_every_division_done(
    db_session: Session,
) -> None:
    service = SeasonService(db_session)
    top = make_division(db_session, level=1)
    bottom = make_division(db_session, level=2)
    for division in (top, bottom):
        home = make_team(db_session, team_name=f"H{division.level}", division_id=division.id)
        away = make_team(db_session, team_name=f"A{division.level}", division_id=division.id)
        make_match(
            db_session,
            division_id=division.id,
            home_team_id=home.id,
            away_team_id=away.id,
        )

    assert service.is_pyramid_complete() is False

    for match in db_session.scalars(select(Match)).all():
        match.played = True
    db_session.commit()
    assert service.is_pyramid_complete() is True


def test_end_season_promotes_and_relegates_between_adjacent_divisions(
    db_session: Session,
) -> None:
    service = SeasonService(db_session)
    top = make_division(db_session, level=1)
    bottom = make_division(db_session, level=2)
    # Distinct points make the final order unambiguous within each division.
    top_teams = {
        name: _standing_team(db_session, division_id=top.id, name=name, points=pts)
        for name, pts in (("A", 12), ("B", 9), ("C", 6), ("D", 3))
    }
    bottom_teams = {
        name: _standing_team(db_session, division_id=bottom.id, name=name, points=pts)
        for name, pts in (("E", 12), ("F", 9), ("G", 6), ("H", 3))
    }

    outcomes = service.end_season()

    db_session.expire_all()
    # Top division: bottom two relegated, nobody promoted (it is the top tier).
    assert top_teams["C"].divisionId == bottom.id
    assert top_teams["D"].divisionId == bottom.id
    assert top_teams["A"].divisionId == top.id
    # Bottom division: top two promoted, nobody relegated (it is the lowest).
    assert bottom_teams["E"].divisionId == top.id
    assert bottom_teams["F"].divisionId == top.id
    assert bottom_teams["G"].divisionId == bottom.id
    # Each division keeps its size after the balanced swap.
    assert _count_in_division(db_session, top.id) == 4
    assert _count_in_division(db_session, bottom.id) == 4

    top_outcome = next(o for o in outcomes if o.level == 1)
    assert top_outcome.championTeamId == top_teams["A"].id
    assert set(top_outcome.relegatedTeamIds) == {top_teams["C"].id, top_teams["D"].id}
    assert top_outcome.promotedTeamIds == []
    bottom_outcome = next(o for o in outcomes if o.level == 2)
    assert set(bottom_outcome.promotedTeamIds) == {
        bottom_teams["E"].id,
        bottom_teams["F"].id,
    }
    assert bottom_outcome.relegatedTeamIds == []


def test_end_season_resets_standings_and_advances_season_with_new_fixtures(
    db_session: Session,
) -> None:
    service = SeasonService(db_session)
    division = make_division(db_session, level=1, season_number=1)
    for name, pts in (("A", 12), ("B", 9), ("C", 6), ("D", 3)):
        _standing_team(db_session, division_id=division.id, name=name, points=pts)

    service.end_season()

    db_session.expire_all()
    refreshed = db_session.get(Division, division.id)
    assert refreshed.seasonNumber == 2
    for team in db_session.scalars(
        select(Team).where(Team.divisionId == division.id)
    ).all():
        assert team.points == 0
        assert team.played == 0
        assert team.goalsFor == 0
    # A single division neither promotes nor relegates, but still gets a fresh
    # fixture list for the new season.
    assert ScheduleService(db_session).has_fixtures(refreshed) is True


def test_end_season_single_division_keeps_all_teams(db_session: Session) -> None:
    service = SeasonService(db_session)
    division = make_division(db_session, level=1)
    teams = [
        _standing_team(db_session, division_id=division.id, name=name, points=pts)
        for name, pts in (("A", 9), ("B", 6), ("C", 3))
    ]

    outcomes = service.end_season()

    db_session.expire_all()
    for team in teams:
        assert team.divisionId == division.id
    assert outcomes[0].promotedTeamIds == []
    assert outcomes[0].relegatedTeamIds == []
    assert outcomes[0].championTeamId == teams[0].id


def test_end_season_no_divisions_is_noop(db_session: Session) -> None:
    assert SeasonService(db_session).end_season() == []


def _count_in_division(db: Session, division_id: uuid.UUID) -> int:
    return len(
        db.scalars(select(Team).where(Team.divisionId == division_id)).all()
    )
