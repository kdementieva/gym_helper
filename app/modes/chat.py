from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)
from app.llm import get_llm

async def chat_message(
    message: str, 
    history: list,
    language: str,) -> tuple[str, list]:
  messages = [
    SystemMessage(
      content=f"""
        You are Gym Helper, a personal fitness and strength training assistant.

        The user's preferred language is {language}.
        Always answer in {language}, unless the user explicitly asks you
        to use another language.

        Answer fitness and training questions clearly and practically.
        Do not invent the user's workout history.
        If answering requires personal workout data, that data should be
        retrieved separately.
        Do not diagnose injuries or medical conditions.
        Acknowledge uncertainty when appropriate.
         """),
    *history,
    HumanMessage(content=message)
  ]

  llm = get_llm(temperature=0.3)
  response = await llm.ainvoke(messages)
  history.append(HumanMessage(content=message))
  history.append(AIMessage(content=response.content))

  return response.content, history