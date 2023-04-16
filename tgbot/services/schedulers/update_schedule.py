import datetime
import logging
import time

from aiogram import Bot
from sqlalchemy import select, text, delete
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.services.database.models import User, Schedule
from tgbot.services.kai_parser.utils import add_group_schedule


async def update_schedule(bot: Bot, db: AsyncSession):
    async with db.begin() as session:
        # get groups to parse
        stm = 'select group_id from selected_group'
        group_ids = (await session.execute(text(stm))).scalars().all()

    for group_id in group_ids:
        async with db.begin() as session:
            await session.execute(delete(Schedule).where(Schedule.group_id == group_id))
        await add_group_schedule(group_id, db)
        logging.debug(f'update schedule for group {group_id} done')
