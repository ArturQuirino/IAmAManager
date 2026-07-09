import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# The six core attributes, in the order used for the derived overall.
ATTRIBUTE_NAMES = (
    "pace",
    "shooting",
    "passing",
    "dribbling",
    "defending",
    "physical",
)


class PlayerPosition(str, enum.Enum):
    GK = "GK"
    DEF = "DEF"
    MID = "MID"
    ATT = "ATT"


class Player(Base):
    __tablename__ = "players"

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
    isStarter: Mapped[bool] = mapped_column(
        "isStarter", Boolean, nullable=False, default=False
    )
    teamId: Mapped[uuid.UUID] = mapped_column(
        "teamId",
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )

    team: Mapped["Team"] = relationship("Team", back_populates="players")

    @property
    def overall(self) -> int:
        """Average of the six core attributes, rounded to the nearest integer.

        Not stored — derived on read so it can never drift from the attributes.
        Uses round-half-up for a predictable result on exact .5 averages.
        """
        total = sum(getattr(self, name) for name in ATTRIBUTE_NAMES)
        return int(total / len(ATTRIBUTE_NAMES) + 0.5)


from app.models.team import Team  # noqa: E402
