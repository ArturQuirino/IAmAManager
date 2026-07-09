import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
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

    team: Mapped["Team | None"] = relationship(
        "Team", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


from app.models.team import Team  # noqa: E402
