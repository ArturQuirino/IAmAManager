import uuid
from datetime import date

from sqlalchemy import JSON, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Match(Base):
    """A single fixture between two teams in a division's season.

    The whole 91-minute simulation is computed in one pass when triggered (see
    docs/match-simulation.md); the per-minute breakdown is preserved in
    `eventLog` purely so the result can be replayed/narrated afterwards.
    Scores stay null and `played` false until the match is simulated.
    """

    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    divisionId: Mapped[uuid.UUID] = mapped_column(
        "divisionId",
        UUID(as_uuid=True),
        ForeignKey("divisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    seasonNumber: Mapped[int] = mapped_column(
        "seasonNumber", Integer, nullable=False
    )
    # The matchday, 1..18 for a 10-team double round-robin (docs/competition.md).
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    homeTeamId: Mapped[uuid.UUID] = mapped_column(
        "homeTeamId",
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    awayTeamId: Mapped[uuid.UUID] = mapped_column(
        "awayTeamId",
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Null until a scheduler (later stage) assigns the real calendar day.
    scheduledDate: Mapped[date | None] = mapped_column(
        "scheduledDate", Date, nullable=True
    )
    # Null until the match is played; set together with `played`.
    homeScore: Mapped[int | None] = mapped_column(
        "homeScore", Integer, nullable=True
    )
    awayScore: Mapped[int | None] = mapped_column(
        "awayScore", Integer, nullable=True
    )
    played: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # Ordered per-minute narration, each entry a structured event carrying a
    # stable outcome code (the frontend owns the translated copy). Null until
    # the match is simulated.
    eventLog: Mapped[list[dict] | None] = mapped_column(
        "eventLog", JSON, nullable=True
    )

    division: Mapped["Division"] = relationship("Division")
    homeTeam: Mapped["Team"] = relationship("Team", foreign_keys=[homeTeamId])
    awayTeam: Mapped["Team"] = relationship("Team", foreign_keys=[awayTeamId])


from app.models.division import Division  # noqa: E402
from app.models.team import Team  # noqa: E402
