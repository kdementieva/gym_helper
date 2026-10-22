from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workout_exercise import WorkoutExercise


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    user: Mapped["User"] = relationship(
        back_populates="workouts"
    )

    workout_exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="workout"
    )