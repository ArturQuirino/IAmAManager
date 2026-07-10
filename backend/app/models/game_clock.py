import enum
from datetime import date

from sqlalchemy import CheckConstraint, Date, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class GameClockId(int, enum.Enum):
    """There is exactly one game clock; its row always carries this id."""

    SINGLETON = 1


class GameClock(Base):
    """A single row tracking the real-time simulation's progress.

    The daily matchday job (see `MatchdayService`) reads and writes this row to
    stay idempotent — it never runs twice for the same calendar day — and to
    drive the weekly cadence (youth academy refresh) off `dayCount`. The table
    holds at most one row, enforced by a check constraint on the primary key.
    """

    __tablename__ = "game_clock"
    __table_args__ = (
        CheckConstraint("id = 1", name="CK_game_clock_singleton"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False,
        default=GameClockId.SINGLETON.value,
    )
    # The last calendar day a matchday was played; null before the first run.
    lastMatchdayDate: Mapped[date | None] = mapped_column(
        "lastMatchdayDate", Date, nullable=True
    )
    # How many matchdays have been played, ever — drives weekly cadence.
    dayCount: Mapped[int] = mapped_column(
        "dayCount", Integer, nullable=False, default=0, server_default="0"
    )
