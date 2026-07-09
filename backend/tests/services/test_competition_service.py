import random

from sqlalchemy.orm import Session

from app.models.player import ATTRIBUTE_NAMES
from app.models.team import Team
from app.services.competition_service import (
    DIVISION_SIZE,
    FAKE_TEAM_SKILL_SCALE,
    CompetitionService,
)
from tests.factories import make_team, make_user


def _service(db: Session) -> CompetitionService:
    return CompetitionService(db, rng=random.Random(1234))


def test_create_division_sets_level_and_season(db_session: Session) -> None:
    division = _service(db_session).create_division(level=3, season_number=2)

    assert division.id is not None
    assert division.level == 3
    assert division.seasonNumber == 2


def test_create_fake_team_is_ownerless_with_full_weak_squad(
    db_session: Session,
) -> None:
    service = _service(db_session)
    division = service.create_division(level=1)

    fake = service.create_fake_team(division)

    assert fake.userId is None
    assert fake.divisionId == division.id
    assert len(fake.players) == 18  # 11 starters + 7 bench
    ceiling = round(100 * FAKE_TEAM_SKILL_SCALE)
    for player in fake.players:
        for attribute in ATTRIBUTE_NAMES:
            assert 1 <= getattr(player, attribute) <= ceiling


def test_fill_division_with_fakes_tops_up_to_division_size(
    db_session: Session,
) -> None:
    service = _service(db_session)
    division = service.create_division(level=1)
    make_team(db_session, team_name="Real FC", division_id=division.id)

    created = service.fill_division_with_fakes(division)

    assert len(created) == DIVISION_SIZE - 1
    assert service.count_teams_in_division(division.id) == DIVISION_SIZE


def test_fill_division_with_fakes_is_noop_when_full(db_session: Session) -> None:
    service = _service(db_session)
    division = service.create_division(level=1)
    service.fill_division_with_fakes(division)

    created = service.fill_division_with_fakes(division)

    assert created == []
    assert service.count_teams_in_division(division.id) == DIVISION_SIZE


def test_get_lowest_division_returns_highest_level(db_session: Session) -> None:
    service = _service(db_session)
    service.create_division(level=1)
    lowest = service.create_division(level=2)

    assert service.get_lowest_division().id == lowest.id


def test_get_lowest_division_none_when_empty(db_session: Session) -> None:
    assert _service(db_session).get_lowest_division() is None


def test_standings_ranked_by_points_then_goal_difference(
    db_session: Session,
) -> None:
    service = _service(db_session)
    division = service.create_division(level=1)
    _make_standing(db_session, division.id, "Leaders", points=9, gf=10, ga=2)
    # Same points as Behind, but a better goal difference — must rank higher.
    _make_standing(db_session, division.id, "GoodGD", points=6, gf=8, ga=2)
    _make_standing(db_session, division.id, "Behind", points=6, gf=4, ga=4)

    standings = service.get_division_standings(division.id)

    assert [team.teamName for team in standings] == ["Leaders", "GoodGD", "Behind"]


def test_standings_only_include_the_requested_division(
    db_session: Session,
) -> None:
    service = _service(db_session)
    division = service.create_division(level=1)
    other = service.create_division(level=2)
    make_team(db_session, team_name="Mine", division_id=division.id)
    make_team(db_session, team_name="Theirs", division_id=other.id)

    standings = service.get_division_standings(division.id)

    assert [team.teamName for team in standings] == ["Mine"]


def _make_user_team(db: Session, *, email: str, team_name: str) -> Team:
    owner = make_user(db, email=email)
    return make_team(db, team_name=team_name, user_id=owner.id)


def test_place_new_team_creates_first_division_with_fakes(
    db_session: Session,
) -> None:
    service = _service(db_session)
    user_team = _make_user_team(
        db_session, email="new@b.com", team_name="Newcomer FC"
    )

    division = service.place_new_team(user_team)

    assert division.level == 1
    assert user_team.divisionId == division.id
    assert service.count_teams_in_division(division.id) == DIVISION_SIZE
    # The user's team plus nine fresh fakes.
    fakes = [team for team in division.teams if team.userId is None]
    assert len(fakes) == DIVISION_SIZE - 1


def test_place_new_team_replaces_fake_and_inherits_its_standing(
    db_session: Session,
) -> None:
    service = _service(db_session)
    division = service.create_division(level=1)
    service.fill_division_with_fakes(division)
    # Make one fake unambiguously the weakest (fewest points) and give it a
    # distinctive standing; that is the slot the newcomer must inherit.
    fakes = sorted(division.teams, key=lambda team: team.id)
    target, *others = fakes
    target.points = 1
    target.played = 5
    target.wins = 0
    target.draws = 1
    target.losses = 4
    target.goalsFor = 6
    target.goalsAgainst = 12
    for other in others:
        other.points = 9
    db_session.commit()
    target_id = target.id
    user_team = _make_user_team(
        db_session, email="new@b.com", team_name="Newcomer FC"
    )

    placed_in = service.place_new_team(user_team)

    assert placed_in.id == division.id
    # Total teams unchanged: one fake out, the user's team in.
    assert service.count_teams_in_division(division.id) == DIVISION_SIZE
    assert db_session.get(Team, target_id) is None
    assert user_team.divisionId == division.id
    assert user_team.points == 1
    assert user_team.played == 5
    assert user_team.draws == 1
    assert user_team.losses == 4
    assert user_team.goalsFor == 6
    assert user_team.goalsAgainst == 12


def test_place_new_team_opens_lower_division_when_lowest_is_full_of_users(
    db_session: Session,
) -> None:
    service = _service(db_session)
    top = service.create_division(level=1)
    # Fill the top division entirely with real (user-owned) teams: no fake slot.
    for index in range(DIVISION_SIZE):
        owner = make_user(db_session, email=f"real{index}@b.com")
        make_team(
            db_session,
            team_name=f"Real {index}",
            user_id=owner.id,
            division_id=top.id,
        )
    user_team = _make_user_team(
        db_session, email="new@b.com", team_name="Newcomer FC"
    )

    division = service.place_new_team(user_team)

    assert division.id != top.id
    assert division.level == top.level + 1
    assert user_team.divisionId == division.id
    assert service.count_teams_in_division(division.id) == DIVISION_SIZE


def _make_standing(
    db: Session,
    division_id,
    name: str,
    *,
    points: int,
    gf: int,
    ga: int,
) -> None:
    team = make_team(db, team_name=name, division_id=division_id)
    team.points = points
    team.goalsFor = gf
    team.goalsAgainst = ga
    db.commit()
