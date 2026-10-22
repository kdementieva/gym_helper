import logging
import sys

import asyncio
from app.telegram_bot import bot, dp, setup_bot_commands

async def main():
   await setup_bot_commands()
   await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())