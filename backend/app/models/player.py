import enum
import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PlayerPosition(str, enum.Enum):
    GK = "GK"
    CB = "CB"
    LB = "LB"
    RB = "RB"
    CDM = "CDM"
    CM = "CM"
    CAM = "CAM"
    LW = "LW"
    RW = "RW"
    ST = "ST"


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
    shirtNumber: Mapped[int] = mapped_column("shirtNumber", Integer, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    nationality: Mapped[str] = mapped_column(String, nullable=False)
    overall: Mapped[int] = mapped_column(Integer, nullable=False)
    userId: Mapped[uuid.UUID] = mapped_column(
        "userId",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="players")


from app.models.user import User  # noqa: E402
