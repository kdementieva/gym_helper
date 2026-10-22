from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.workout import Workout


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False
    )

    username: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True
    )

    first_name: Mapped[str] = mapped_column(
        String(64)
    )

    language_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True
    )

    preferred_language: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    workouts: Mapped[list["Workout"]] = relationship(
        back_populates="user"
    )

    conversation_messages = relationship(
        "ConversationMessage",
        back_populates="user",
        cascade="all, delete-orphan",
    )