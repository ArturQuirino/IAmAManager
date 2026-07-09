import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
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
    # Null while a team is being placed; a team always ends up in exactly one
    # division. ON DELETE SET NULL so removing a division never cascades into
    # deleting its teams.
    divisionId: Mapped[uuid.UUID | None] = mapped_column(
        "divisionId",
        UUID(as_uuid=True),
        ForeignKey("divisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Season standing, accumulated as matches are played (match simulation is a
    # later stage; these start at zero and stay there until then).
    points: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    played: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    wins: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    draws: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    losses: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    goalsFor: Mapped[int] = mapped_column(
        "goalsFor", Integer, nullable=False, default=0, server_default="0"
    )
    goalsAgainst: Mapped[int] = mapped_column(
        "goalsAgainst", Integer, nullable=False, default=0, server_default="0"
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
    division: Mapped["Division | None"] = relationship(
        "Division", back_populates="teams"
    )
    players: Mapped[list["Player"]] = relationship(
        "Player", back_populates="team", cascade="all, delete-orphan"
    )
    youth_candidates: Mapped[list["YouthCandidate"]] = relationship(
        "YouthCandidate", back_populates="team", cascade="all, delete-orphan"
    )

    @property
    def goalDifference(self) -> int:
        """Goals scored minus goals conceded — the first standings tie-break."""
        return self.goalsFor - self.goalsAgainst


from app.models.division import Division  # noqa: E402
from app.models.player import Player  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.youth_candidate import YouthCandidate  # noqa: E402
