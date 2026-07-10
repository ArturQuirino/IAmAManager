from datetime import datetime

from app.scheduler import SECONDS_PER_DAY, _seconds_until_next_run


def test_seconds_until_next_run_later_today() -> None:
    now = datetime(2026, 7, 9, 12, 0, 0)

    seconds = _seconds_until_next_run(now, hour=18, minute=0)

    assert seconds == 6 * 60 * 60


def test_seconds_until_next_run_rolls_to_tomorrow_when_time_has_passed() -> None:
    now = datetime(2026, 7, 9, 19, 0, 0)

    seconds = _seconds_until_next_run(now, hour=18, minute=0)

    assert seconds == 23 * 60 * 60


def test_seconds_until_next_run_at_exact_time_waits_a_full_day() -> None:
    now = datetime(2026, 7, 9, 18, 0, 0)

    seconds = _seconds_until_next_run(now, hour=18, minute=0)

    assert seconds == SECONDS_PER_DAY
