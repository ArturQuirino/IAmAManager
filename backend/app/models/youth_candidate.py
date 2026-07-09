import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.player import ATTRIBUTE_NAMES, PlayerPosition


class YouthCandidate(Base):
    """A weekly youth-academy prospect a team may promote into its squad.

    Shares the six-attribute / four-position shape of `Player`. Candidates not
    added before the next weekly refresh are discarded, so they live only until
    `YouthService.refresh_week` regenerates the batch.
    """

    __tablename__ = "youth_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[PlayerPosition] = mapped_column(
        ENUM(PlayerPosition, name="players_position_enum", create_type=False),
        nullable=False,
    )
    pace: Mapped[int] = mapped_column(Integer, nullable=False)
    shooting: Mapped[int] = mapped_column(Integer, nullable=False)
    passing: Mapped[int] = mapped_column(Integer, nullable=False)
    dribbling: Mapped[int] = mapped_column(Integer, nullable=False)
    defending: Mapped[int] = mapped_column(Integer, nullable=False)
    physical: Mapped[int] = mapped_column(Integer, nullable=False)
    # The Monday (or generation date) of the week this batch belongs to; lets a
    # refresh target the current week and a scheduler avoid regenerating twice.
    weekOf: Mapped[date] = mapped_column("weekOf", Date, nullable=False)
    teamId: Mapped[uuid.UUID] = mapped_column(
        "teamId",
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )

    team: Mapped["Team"] = relationship("Team", back_populates="youth_candidates")

    @property
    def overall(self) -> int:
        """Average of the six core attributes, rounded — same rule as Player."""
        total = sum(getattr(self, name) for name in ATTRIBUTE_NAMES)
        return int(total / len(ATTRIBUTE_NAMES) + 0.5)


from app.models.team import Team  # noqa: E402
