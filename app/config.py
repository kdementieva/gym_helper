import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_GPT = os.getenv("OPENAI_API_GPT")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")