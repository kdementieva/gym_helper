from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage

from app.llm import get_llm


class LanguageResult(BaseModel):
    language: str


async def normalize_language(user_input: str) -> str:
    llm = get_llm(temperature=0)

    structured_llm = llm.with_structured_output(
        LanguageResult,
        method="function_calling",
    )

    result = await structured_llm.ainvoke([
        SystemMessage(content="""
          The user is selecting the language they want to use.

          Determine which language they mean.
          Return the standard English name of the language.

          Examples:
          "русский" -> "Russian"
          "українська" -> "Ukrainian"
          "polski" -> "Polish"
          "Deutsch" -> "German"
          "日本語" -> "Japanese"

          Do not answer the user.
          Only identify the language.
          """),
        HumanMessage(content=user_input),
    ])

    return result.language


async def create_welcome_message(
    language: str,
    first_name: str | None,
) -> str:
    llm = get_llm(temperature=0.5)

    response = await llm.ainvoke([
        SystemMessage(content=f"""
          You are Gym Helper, a friendly personal AI fitness assistant.

          The user's preferred language is: {language}.
          Write the entire response naturally in that language.

          Create a short welcome message for a Telegram bot.

          The message should:
          - greet the user by first name if available;
          - introduce Gym Helper in one short sentence;
          - explain that the user can simply talk to you like to a personal trainer;
          - briefly show the main capabilities:
            🏋️ save workouts from text or screenshots;
            📈 analyze workout history and progress;
            💬 help with training decisions based on workout history;
            🔎 search for current research when needed;

          Formatting rules:
          - keep it short and easy to scan;
          - use short paragraphs;
          - use exactly one emoji for each capability;
          - put each capability on a separate line;
          - do not write long paragraphs;
          - do not use Markdown;
          - do not mention LLMs, databases, APIs, tools, agents, routing,
            or other implementation details;
          - do not sound corporate or overly formal;
          - do not make medical claims.
          """),
        HumanMessage(
            content=f"User's first name: {first_name or 'unknown'}"
        ),
    ])

    return response.content

async def system_message(
    language: str,
    meaning: str,
) -> str:
    llm = get_llm(temperature=0)

    response = await llm.ainvoke([
        SystemMessage(content=f"""
          You generate very short UI messages for Gym Helper.

          The user's preferred language is {language}.

          Write the requested message naturally in {language}.

          Rules:
          - preserve the exact meaning;
          - keep it short;
          - do not add explanations;
          - do not add information that was not requested;
          - return only the message shown to the user.
          """),
        HumanMessage(content=meaning),
    ])

    return response.content.strip()