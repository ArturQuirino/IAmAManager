import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    teamName: Mapped[str] = mapped_column("teamName", String, nullable=False)
    # Null userId marks a fake (CPU-controlled) team, which has no owner.
    userId: Mapped[uuid.UUID | None] = mapped_column(
        "userId",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    # Nullable until the competition layer (Etapa 1) introduces the divisions
    # table; kept as a plain column here to avoid a forward FK dependency.
    divisionId: Mapped[uuid.UUID | None] = mapped_column(
        "divisionId", UUID(as_uuid=True), nullable=True
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

    user: Mapped["User | None"] = relationship("User", back_populates="team")
    players: Mapped[list["Player"]] = relationship(
        "Player", back_populates="team", cascade="all, delete-orphan"
    )


from app.models.player import Player  # noqa: E402
from app.models.user import User  # noqa: E402
