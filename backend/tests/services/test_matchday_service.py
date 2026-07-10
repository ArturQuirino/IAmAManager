import random
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.division import Division
from app.models.game_clock import GameClock, GameClockId
from app.models.match import Match
from app.models.team import Team
from app.models.youth_candidate import YouthCandidate
from app.services.matchday_service import (
    YOUTH_REFRESH_INTERVAL_DAYS,
    MatchdayService,
)
from app.services.schedule_service import ScheduleService
from tests.factories import make_division, make_starting_xi, make_team, make_user_with_team


def _two_team_division(db: Session) -> tuple[Division, Team, Team]:
    """A one-division world: a user team and a fake opponent, both match-ready.

    Two teams double-round-robin to two rounds of one match each, so a season
    completes in two matchdays — enough to exercise turnover cheaply.
    """
    division = make_division(db, level=1)
    _, team = make_user_with_team(db, team_name="Mine FC")
    team.divisionId = division.id
    opponent = make_team(db, team_name="Rival FC", division_id=division.id)
    db.commit()
    make_starting_xi(db, team.id, prefix="M")
    make_starting_xi(db, opponent.id, prefix="R")
    ScheduleService(db).generate_double_round_robin(division)
    return division, team, opponent


def _service(db: Session, *, day: date) -> MatchdayService:
    return MatchdayService(db, rng=random.Random(1), today=lambda: day)


def _played_count(db: Session) -> int:
    return len(db.scalars(select(Match).where(Match.played.is_(True))).all())


def test_run_plays_the_next_round(db_session: Session) -> None:
    _two_team_division(db_session)

    report = _service(db_session, day=date(2026, 1, 1)).run_due_matchday()

    assert report.ran is True
    assert report.matchesPlayed == 1
    assert report.seasonEnded is False
    assert _played_count(db_session) == 1


def test_run_is_idempotent_within_the_same_day(db_session: Session) -> None:
    _two_team_division(db_session)
    service = _service(db_session, day=date(2026, 1, 1))
    service.run_due_matchday()

    report = service.run_due_matchday()

    assert report.ran is False
    assert report.matchesPlayed == 0
    # Still just the single round-one match — the day was not replayed.
    assert _played_count(db_session) == 1


def test_consecutive_days_advance_rounds_and_end_the_season(
    db_session: Session,
) -> None:
    division, _, _ = _two_team_division(db_session)

    _service(db_session, day=date(2026, 1, 1)).run_due_matchday()
    report = _service(db_session, day=date(2026, 1, 2)).run_due_matchday()

    assert report.seasonEnded is True
    db_session.expire_all()
    refreshed = db_session.get(Division, division.id)
    assert refreshed.seasonNumber == 2
    # Both first-season matches are done; a fresh unplayed season-two fixture
    # list has been laid out.
    assert _played_count(db_session) == 2
    unplayed = db_session.scalars(
        select(Match).where(Match.played.is_(False))
    ).all()
    assert all(match.seasonNumber == 2 for match in unplayed)
    assert len(unplayed) == 2


def test_no_youth_refresh_on_a_non_weekly_day(db_session: Session) -> None:
    _, team, _ = _two_team_division(db_session)

    report = _service(db_session, day=date(2026, 1, 1)).run_due_matchday()

    assert report.youthRefreshed is False
    assert _candidate_count(db_session, team.id) == 0


def test_weekly_youth_refresh_hits_user_teams_only(db_session: Session) -> None:
    _, team, opponent = _two_team_division(db_session)
    # Start the clock one day short of a full week so the next run crosses the
    # weekly boundary without looping through seven matchdays.
    db_session.add(
        GameClock(
            id=GameClockId.SINGLETON.value,
            dayCount=YOUTH_REFRESH_INTERVAL_DAYS - 1,
            lastMatchdayDate=date(2026, 1, 6),
        )
    )
    db_session.commit()

    report = _service(db_session, day=date(2026, 1, 7)).run_due_matchday()

    assert report.youthRefreshed is True
    # One prospect per position for the user team; fake teams have no academy.
    assert _candidate_count(db_session, team.id) == 4
    assert _candidate_count(db_session, opponent.id) == 0


def _candidate_count(db: Session, team_id) -> int:
    return len(
        db.scalars(
            select(YouthCandidate).where(YouthCandidate.teamId == team_id)
        ).all()
    )
