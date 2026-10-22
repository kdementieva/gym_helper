from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from datetime import datetime
from app.llm import get_llm
from app.schemas.workout import WorkoutData
from app.tools import create_workout_tools
import base64



llm = get_llm(temperature=0)

structured_llm = llm.with_structured_output(
    WorkoutData,
    method="function_calling"
)

async def parse_workout(message: str) -> WorkoutData:
    now = datetime.now()
    
    messages = [
        SystemMessage(
            content=f"""
            Extract workout data from the user's message.

            Current date and time: {now.isoformat()}

            Do not invent information that the user did not provide.
            If optional information such as weight, RIR or notes is missing,
            leave it empty.
            """
        ),
        HumanMessage(content=message),
    ]

    result = await structured_llm.ainvoke(messages)

    return result


async def analyze_workout(
        message:str,
        history: list,
        session,
        user_id: int,
        language: str,
) -> str:
    tools = create_workout_tools(
        session=session,
        user_id=user_id
    )

    tools_by_name = {
        tool.name: tool
        for tool in tools
    }

    llm_with_tools = llm.bind_tools(tools)
    messages = [
        SystemMessage(content=f"""
        You are Gym Helper, an experienced AI fitness coach.

        The user's preferred language is {language}.
        Always respond in that language unless explicitly
        asked otherwise.

        You have access to tools for:
        - Retrieving the user's workout history.
        - Retrieving their latest workout.
        - Searching the internet for fitness research.

        TOOL USAGE:

        1. For personalized progression questions:
        Retrieve relevant workout history before
        recommending changes in weight or repetitions.

        2. For questions about scientific evidence,
        current recommendations, or research:
        Use the web search tool.

        3. You may call multiple tools for one question.
        Combine personal workout data with research
        when both are relevant.

        4. Do not search the web unnecessarily.
        Simple questions should not require research.

        5. Never invent workout history, RIR values,
        research findings, or scientific sources.

        6. If the user's history is insufficient,
        explain what information is missing
        and ask a relevant follow-up question.

        7. When recommending weight progression,
        consider previous workouts, sets, reps,
        technique, recovery, and RIR when available.

        8. If you use research, distinguish general
        scientific guidance from recommendations
        based on the user's personal data.
        Include source links when available.

        Be conversational, concise, and practical.
        """),
        *history,
        HumanMessage(content=message),
    ]

    max_iterations = 5

    for _ in range(max_iterations):
        response = await llm_with_tools.ainvoke(
            messages
        )

        messages.append(response)
        if not response.tool_calls:
            return response.content

        for tool_call in response.tool_calls:
            tool_name = tool_call['name']
            tool = tools_by_name.get(tool_name)

            if tool is None:
                messages.append(
                    ToolMessage(
                        content=(
                            f"""Tool '{tool_name}' does not exists."""
                        ),
                        tool_call_id=tool_call['id'],
                    )
                )
                continue

            result = await tool.ainvoke(tool_call['args'])

            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call['id'],
                )
            )
    return (
        ''' I couldn't complete the workout analysis
        because too many tool calls were required'''
    )

async def parse_workout_images(
    images: list[bytes],
) -> WorkoutData:
    now = datetime.now()

    content = [
        {
            "type": "text",
            "text": (
                "These screenshots belong to ONE workout. "
                "Extract the complete workout from all images."
            ),
        }
    ]

    for image_bytes in images:
        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        content.append({
            "type": "image_url",
            "image_url": {
                "url": (
                    "data:image/jpeg;base64,"
                    + image_base64
                )
            },
        })

    messages = [
        SystemMessage(
            content=f"""
            Extract workout data from the screenshots.

            Current date and time:
            {now.isoformat()}

            IMPORTANT:
            All provided screenshots belong to ONE workout.

            Analyze all screenshots together.

            A workout may continue from one screenshot
            to another.

            The same exercise may appear on multiple
            screenshots because screenshots can overlap.

            Do not duplicate an exercise or set simply
            because it is visible on multiple screenshots.

            Combine the screenshots into one complete
            WorkoutData object.

            Read only information actually visible.

            Do not invent missing values.

            Weight:
            - numeric value only
            - never include kg, кг, lb or lbs

            Repetitions:
            - integer only

            RIR:
            - integer or empty

            Preserve the exercise order when it can be
            determined from the screenshots.
            """
        ),
        HumanMessage(content=content),
    ]

    return await structured_llm.ainvoke(messages)

def format_workout(workout: WorkoutData) -> str:
    lines = []

    for exercise in workout.exercises:
        lines.append(
            f"{exercise.exercise_order}. {exercise.name}"
        )

        for exercise_set in exercise.sets:
            if exercise_set.weight is not None:
                set_text = (
                    f"{exercise_set.set_number}. "
                    f"{exercise_set.weight} kg × "
                    f"{exercise_set.reps}"
                )
            else:
                set_text = (
                    f"{exercise_set.set_number}. "
                    f"{exercise_set.reps}"
                )

            if exercise_set.rir is not None:
                set_text += f", RIR {exercise_set.rir}"

            lines.append(set_text)

        if exercise.notes:
            lines.append(exercise.notes)

        lines.append("")

    return "\n".join(lines).strip()

async def correct_workout(
    workout: WorkoutData,
    correction: str,
) -> WorkoutData:

    messages = [
        SystemMessage(
            content="""
            You are editing already extracted workout data.

            Apply only the correction explicitly requested
            by the user.

            Keep all other workout data unchanged.

            Do not invent new exercises, sets, weights,
            repetitions, RIR values, dates, or notes.

            Weight must contain only a numeric value,
            without units such as kg, кг, lb or lbs.

            If the user's correction is ambiguous,
            do not guess.
            """
        ),
        HumanMessage(
            content=f"""
            Current workout:

            {workout.model_dump_json()}

            User correction:

            {correction}
            """
        ),
    ]

    result = await structured_llm.ainvoke(messages)

    return result