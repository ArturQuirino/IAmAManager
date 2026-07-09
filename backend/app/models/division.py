import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# Level 1 is the top tier; larger numbers are progressively lower divisions.
TOP_DIVISION_LEVEL = 1


class Division(Base):
    __tablename__ = "divisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    seasonNumber: Mapped[int] = mapped_column(
        "seasonNumber", Integer, nullable=False
    )
    createdAt: Mapped[datetime] = mapped_column(
        "createdAt", DateTime, server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        "updatedAt",
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    teams: Mapped[list["Team"]] = relationship("Team", back_populates="division")


from app.models.team import Team  # noqa: E402
