from langchain_tavily import TavilySearch
from langchain_core.tools import tool

from app.services.workouts import (
    get_exercise_history,
    get_last_workout,
    get_recent_workouts,
    get_user_exercise_names,
)

from app.config import TAVILY_API_KEY


tavily = TavilySearch(
    api_key=TAVILY_API_KEY,
    max_results=5,
)


def create_workout_tools(
    session,
    user_id: int,
):

    @tool
    async def search_training_research(query: str) -> str:
        """
        Search the internet for exercise science,
        strength training, hypertrophy, recovery,
        and evidence-based fitness recommendations.

        Use this tool when the user asks for research,
        scientific evidence, recent information,
        or when external information is necessary.

        Do not use it for questions that can be
        answered using the user's workout history.
        """
        result = await tavily.ainvoke({
            "query": query
        })

        return str(result)

    @tool
    async def exercise_history(
        exercise_name: str,
    ) -> list[dict]:
        """
        Get the current user's recent history for one specific exercise.

        Use this when you know the exact exercise name stored in the
        user's workout history.

        If you are unsure which stored exercise the user means,
        use list_user_exercises first.
        """
        return await get_exercise_history(
            session=session,
            user_id=user_id,
            exercise_name=exercise_name,
        )

    @tool
    async def last_workout() -> dict | None:
        """
        Get the current user's most recent workout including
        all exercises, sets, weights, repetitions and RIR values.

        Use this when the user asks about their last workout.
        """
        return await get_last_workout(
            session=session,
            user_id=user_id,
        )

    @tool
    async def recent_workouts(
        limit: int = 5,
    ) -> list[dict]:
        """
        Get several of the current user's most recent workouts.

        Use this when the user asks to compare workouts or analyze
        changes across multiple workout sessions.
        """
        limit = max(1, min(limit, 10))

        return await get_recent_workouts(
            session=session,
            user_id=user_id,
            limit=limit,
        )

    @tool
    async def list_user_exercises() -> list[str]:
        """
        Get all exercise names that exist in the current user's
        workout history.

        Use this when the user refers to an exercise using an
        informal, translated, abbreviated or potentially different
        name and you need to determine which stored exercise they mean.

        If several stored exercises could match, ask the user
        which exercise they mean instead of guessing.
        """
        return await get_user_exercise_names(
            session=session,
            user_id=user_id,
        )

    return [
        exercise_history,
        last_workout,
        recent_workouts,
        list_user_exercises,
        search_training_research,
    ]