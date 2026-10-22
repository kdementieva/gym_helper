from langchain_openai import ChatOpenAI

from app.config import OPENAI_API_GPT

def get_llm(temperature=0.3):
  return ChatOpenAI(
    model="gpt-4o",
    temperature=temperature,
    api_key=OPENAI_API_GPT,
)
