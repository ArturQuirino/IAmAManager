import asyncio
import logging
from datetime import datetime, timedelta

from app.config.settings import get_settings
from app.database.session import SessionLocal
from app.services.matchday_service import MatchdayService

logger = logging.getLogger(__name__)

SECONDS_PER_DAY = 24 * 60 * 60


def _seconds_until_next_run(now: datetime, *, hour: int, minute: int) -> float:
    """Seconds from `now` until the next occurrence of `hour:minute` local time."""
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _run_matchday_once() -> None:
    """Open a short-lived session and advance the world by (at most) one day.

    `MatchdayService` is idempotent per calendar day, so a spurious extra wake
    (or a restart) never double-plays a round.
    """
    db = SessionLocal()
    try:
        MatchdayService(db).run_due_matchday()
    finally:
        db.close()


async def _scheduler_loop(*, hour: int, minute: int) -> None:
    while True:
        delay = _seconds_until_next_run(
            datetime.now(), hour=hour, minute=minute
        )
        await asyncio.sleep(delay)
        try:
            await asyncio.to_thread(_run_matchday_once)
        except Exception:  # noqa: BLE001 — a job failure must not kill the loop
            logger.exception("Scheduled matchday run failed")


def start_scheduler() -> asyncio.Task | None:
    """Start the daily matchday loop if enabled; otherwise do nothing.

    Returns the created task (so the caller can cancel it on shutdown) or None
    when the scheduler is disabled. Configuration lives entirely in settings.
    """
    settings = get_settings()
    if not settings.is_scheduler_enabled:
        logger.info("Matchday scheduler disabled")
        return None

    logger.info(
        "Matchday scheduler enabled — firing daily at %02d:%02d",
        settings.matchday_hour,
        settings.matchday_minute,
    )
    return asyncio.create_task(
        _scheduler_loop(
            hour=settings.matchday_hour, minute=settings.matchday_minute
        )
    )
