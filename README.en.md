# Gym Helper

**English** | [Русский](README.md)

An AI Telegram bot for logging strength workouts, reviewing progress, and answering fitness questions. Interact through natural language messages without separate commands for every task.

## Features

- Extract exercises, sets, weights, repetitions, and RIR from text.
- Read workouts from a single screenshot or multiple screenshots sent as an album.
- Preview workouts before saving: confirm, describe a correction, or cancel.
- Store workouts and conversation history in PostgreSQL.
- Analyze the latest workout, exercise history, and several recent workouts.
- Answer training questions using recent conversation context.
- Search for studies through Tavily and combine scientific evidence with personal workout history in one answer.
- Run in-depth research with multiple search tasks for detailed reviews and comparative reports.
- Choose a language with `/start`, retain that preference, and change it with `/language`.

## Tech stack

Python, aiogram, LangChain, LangGraph, OpenAI, Tavily, PostgreSQL 17, SQLAlchemy, and Alembic. The current model is `gpt-4o`, configured in [`app/llm.py`](app/llm.py).

## Run locally

You will need Python 3.11+ (recommended), Docker with Compose, a Telegram bot token, and OpenAI and Tavily API keys.

### 1. Install dependencies

From the cloned repository directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with `.\.venv\Scripts\Activate.ps1`.

### 2. Configure the environment

Copy `.env.template` to `.env` and fill in these values:

```dotenv
OPENAI_API_GPT=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql+asyncpg://gym_helper:gym_helper@localhost:5433/gym_helper
```

Set the OpenAI key through `OPENAI_API_GPT`, read by [`app/config.py`](app/config.py).

Create a Telegram bot token through `@BotFather`. Keep `.env` and real API keys out of the repository. The example database settings match the local `docker-compose.yml`.

### 3. Start the database and apply migrations

```bash
docker compose up -d postgres
python -m alembic upgrade head
```

Wait for PostgreSQL to become ready before running migrations. Compose starts only the database; its data is persisted in the `postgres_data` Docker volume. The database is exposed on local port `5433`.

### 4. Start the bot

```bash
python main.py
```

The bot receives messages through long polling. At startup, it registers `/start` and `/language` in the Telegram command menu. Open the bot, send `/start`, and enter your preferred language if you have not selected one yet.

## Commands

| Command | Action |
| --- | --- |
| `/start` | Starts the conversation: asks for a language if none is selected, or shows a welcome message in the saved language. |
| `/language` | Asks you to enter a new language, such as “English”, “русский”, or “polski”. The preference is saved in the database. |

Use ordinary messages to log workouts, request analysis, or search for research. The bot selects the appropriate mode automatically.

## Usage examples

```text
Log my workout: squats at 60 kg, 3 sets of 8 reps, RIR 2.
```

Review the extracted data and press ✅ to save, ✏️ to edit, or ❌ to cancel. For example, describe a correction as “The second set was 10 reps.”

You can also send one screenshot or an album containing multiple screenshots of the same workout. After saving, ask:

```text
What weight did I use for squats last time?
Compare my recent workouts.
Find studies about training to failure.
Analyze my squats and compare them with current research.
```

The analysis mode can retrieve workout history and search for research, combining both in one answer. It may ask for clarification when the available data is insufficient. When using research, it is instructed to include source links when available.

For a detailed review, explicitly request in-depth research, for example:

```text
Conduct an in-depth literature review of hypertrophy research from 2020 to 2026.
Prepare a detailed comparative report on five strength training methodologies.
```

These requests use a separate LangGraph workflow: planning search tasks, searching through Tavily, evaluating completeness, and preparing the final answer. Ordinary questions about research are handled in analysis mode.

## Project structure

```text
app/
  telegram_bot.py     Telegram handlers and workout confirmation
  router.py           User intent classification
  llm.py              Model configuration
  modes/              Chat, workouts, research, and language selection
  models/             Database models
  schemas/            Pydantic workout schemas
  services/           Users, conversation history, and workout storage
  states/             Conversation states
  tools.py            Training research search and workout history tools
migration/            Alembic migrations
docker-compose.yml    Local PostgreSQL service
main.py               Entry point
```

## Verification and current limitations

`test_workout_history.py` and `test_tools.py` are manual integration scripts. They require a configured environment, a migrated database, and workout data for `user_id=1`; `test_tools.py` also calls OpenAI.

```bash
python test_workout_history.py
python test_tools.py
```

Workout drafts and conversation states are kept in process memory and are lost on restart. Saved workouts and messages remain in PostgreSQL. The latest 10 messages are loaded for conversation context.

Text and images are processed through OpenAI, while search queries are handled by Tavily. External API calls require network access and may incur provider charges.
