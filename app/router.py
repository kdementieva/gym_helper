from app.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage


async def router_message(message: str, history: list) -> str:
    messages = [
        SystemMessage(content="""
        Classify the user's latest message into exactly one category.

        Use conversation history to resolve references such as
        "it", "this exercise", "это", "их", "про него".

        Classify the latest message's intent, not older messages.

        CHAT:
        General conversation and simple fitness questions
        that do not require personal workout history or
        external research.

        Examples:
        - "Hello!"
        - "What is RIR?"
        - "How many sets should beginners do?"
        - "Привет, как дела?"

        WORKOUT_LOG:
        The user is providing completed workout data
        that should be recorded.

        Examples:
        - "Leg press: 50x12, 55x10, 55x9 RIR 1"
        - "Today I did squats 3x8 at 60 kg"
        - "Запиши тренировку: жим ногами 50 кг на 12"

        WORKOUT_ANALYSIS:
        Questions requiring personal workout history,
        progression analysis, or fitness-related web research.

        This category includes:
        - Personal workout analysis.
        - Comparing exercises or training sessions.
        - Strength and hypertrophy research.
        - Exercise science and recovery.
        - Scientific studies about fitness.
        - Questions combining workout history with research.

        Examples:
        - "Should I increase the weight on leg press?"
        - "How am I progressing?"
        - "Find recent studies about RIR"
        - "What does research say about muscle failure?"
        - "Analyze my squats and compare with current research"
        - "Что говорят исследования о тренировках до отказа?"

        RESEARCH:
        Complex, multi-step research requiring several
        independent searches, source comparisons,
        or a detailed research report.

        Use this category only when the user explicitly
        requests deep research or an extensive report.

        Examples:
        - "Conduct an in-depth literature review of
        hypertrophy research from 2020 to 2026"
        - "Prepare a detailed comparative report on
        five different training methodologies"
        - "Проведи глубокое исследование влияния
        тренировок на гормональную систему"

        IMPORTANT:
        A request for scientific studies or sources
        does NOT automatically mean RESEARCH.

        For ordinary fitness research, prefer WORKOUT_ANALYSIS.

        Return exactly one of:
        CHAT
        WORKOUT_LOG
        WORKOUT_ANALYSIS
        RESEARCH
        """),
        *history,
        HumanMessage(content=message)
    ]

    llm = get_llm(temperature=0)
    result = await llm.ainvoke(messages)

    return result.content.strip()