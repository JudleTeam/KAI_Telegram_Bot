import asyncio

import aioschedule
from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.services.schedulers.update_schedule import update_schedule


async def start_schedulers(bot: Bot, session: async_sessionmaker):
    # prod
    aioschedule.every().day.at('3:00').do(update_schedule, bot, session)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)
