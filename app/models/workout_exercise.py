from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.workout import Workout
    from app.models.exercise_set import ExerciseSet


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    workout_id: Mapped[int] = mapped_column(
        ForeignKey("workouts.id")
    )

    name: Mapped[str] = mapped_column(
        String(150)
    )

    exercise_order: Mapped[int] = mapped_column(
        Integer
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    workout: Mapped["Workout"] = relationship(
        back_populates="workout_exercises"
    )

    exercise_sets: Mapped[list["ExerciseSet"]] = relationship(
        back_populates="workout_exercise"
    )