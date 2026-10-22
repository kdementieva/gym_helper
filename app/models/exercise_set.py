from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.workout_exercise import WorkoutExercise


class ExerciseSet(Base):
    __tablename__ = "exercise_sets"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    workout_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("workout_exercises.id")
    )

    set_number: Mapped[int] = mapped_column(
        Integer
    )

    weight: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True
    )

    reps: Mapped[int] = mapped_column(
        Integer
    )

    rir: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    workout_exercise: Mapped["WorkoutExercise"] = relationship(
        back_populates="exercise_sets"
    )