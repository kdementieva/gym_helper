from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workout import Workout
from app.models.workout_exercise import WorkoutExercise
from app.models.exercise_set import ExerciseSet
from app.schemas.workout import WorkoutData

from sqlalchemy.orm import selectinload
from sqlalchemy import select


async def create_workout(
    session: AsyncSession,
    user_id: int,
    date: datetime,
    notes: str | None = None,
) -> Workout:

    workout = Workout(
        user_id=user_id,
        date=date,
        notes=notes,
    )

    session.add(workout)

    await session.commit()
    await session.refresh(workout)

    return workout


async def save_workout(
    session: AsyncSession, 
    user_id: int,
    data: WorkoutData,) -> Workout:

    workout = Workout(
        user_id=user_id,
        date=data.date,
        notes=data.notes,
    )

    for exercise_data in data.exercises:
        exercise = WorkoutExercise(
            name=exercise_data.name,
            exercise_order=exercise_data.exercise_order,
            notes=exercise_data.notes,
        )

        for set_data in exercise_data.sets:
            exercise_set = ExerciseSet(
                set_number=set_data.set_number,
                weight=set_data.weight,
                reps=set_data.reps,
                rir=set_data.rir,
            )

            exercise.exercise_sets.append(exercise_set)

        workout.workout_exercises.append(exercise)

    session.add(workout)

    await session.commit()
    await session.refresh(workout)

    return workout

    
async def get_exercise_history(
        session: AsyncSession,
        user_id: int,
        exercise_name: str,
        limit: int = 5,
):
    result = await session.execute(
        select(WorkoutExercise)
        .join(Workout)
        .where(
            Workout.user_id == user_id,
            WorkoutExercise.name.ilike(exercise_name),
        )
        .options(
            selectinload(WorkoutExercise.exercise_sets),
            selectinload(WorkoutExercise.workout),
        )
        .order_by(Workout.date.desc())
        .limit(limit)
    )

    exercises = result.scalars().all()

    history = []

    for exercise in exercises:
        history.append({
            "date": exercise.workout.date.isoformat(),
            "exercise": exercise.name,
            "sets": [
                {
                    "set_number": exercise_set.set_number,
                    "weight": (
                        float(exercise_set.weight)
                        if exercise_set.weight is not None
                        else None
                    ),
                    "reps": exercise_set.reps,
                    "rir": exercise_set.rir,
                }
                for exercise_set in exercise.exercise_sets
            ],
        })

    return history


async def get_last_workout(
    session,
    user_id: int,
) -> dict | None:
    result = await session.execute(
        select(Workout)
        .where(
            Workout.user_id == user_id
        )
        .options(
            selectinload(Workout.workout_exercises)
            .selectinload(WorkoutExercise.exercise_sets)
        )
        .order_by(Workout.date.desc())
        .limit(1)
    )

    workout = result.scalar_one_or_none()

    if workout is None:
        return None

    return {
        "date": workout.date.isoformat(),
        "notes": workout.notes,
        "exercises": [
            {
                "name": exercise.name,
                "notes": exercise.notes,
                "sets": [
                    {
                        "set_number": exercise_set.set_number,
                        "weight": (
                            float(exercise_set.weight)
                            if exercise_set.weight is not None
                            else None
                        ),
                        "reps": exercise_set.reps,
                        "rir": exercise_set.rir,
                    }
                    for exercise_set in exercise.exercise_sets
                ],
            }
            for exercise in workout.workout_exercises
        ],
    }


async def get_recent_workouts(
    session,
    user_id: int,
    limit: int = 5,
) -> list[dict]:
    result = await session.execute(
        select(Workout)
        .where(
            Workout.user_id == user_id
        )
        .options(
            selectinload(Workout.workout_exercises)
            .selectinload(WorkoutExercise.exercise_sets)
        )
        .order_by(Workout.date.desc())
        .limit(limit)
    )

    workouts = result.scalars().all()

    return [
        {
            "date": workout.date.isoformat(),
            "notes": workout.notes,
            "exercises": [
                {
                    "name": exercise.name,
                    "notes": exercise.notes,
                    "sets": [
                        {
                            "set_number": exercise_set.set_number,
                            "weight": (
                                float(exercise_set.weight)
                                if exercise_set.weight is not None
                                else None
                            ),
                            "reps": exercise_set.reps,
                            "rir": exercise_set.rir,
                        }
                        for exercise_set in exercise.exercise_sets
                    ],
                }
                for exercise in workout.workout_exercises
            ],
        }
        for workout in workouts
    ]


async def get_user_exercise_names(
    session,
    user_id: int,
) -> list[str]:
    result = await session.execute(
        select(WorkoutExercise.name)
        .join(Workout)
        .where(
            Workout.user_id == user_id
        )
        .distinct()
        .order_by(WorkoutExercise.name)
    )

    return list(result.scalars().all())