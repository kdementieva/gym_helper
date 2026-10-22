from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ExerciseSetData(BaseModel):
    set_number: int
    weight: Decimal | None = None
    reps: int
    rir: int | None = None


class ExerciseData(BaseModel):
    name: str
    exercise_order: int
    notes: str | None = None
    sets: list[ExerciseSetData]


class WorkoutData(BaseModel):
    date: datetime
    notes: str | None = None
    exercises: list[ExerciseData]