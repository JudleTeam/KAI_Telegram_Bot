import datetime
import logging
import time

from aiogram import Bot
from sqlalchemy import select, text, delete
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.services.database.models import User, GroupLesson
from tgbot.services.kai_parser.utils import add_group_schedule


async def update_schedule(bot: Bot, db: AsyncSession):
    async with db.begin() as session:
        groups = await User.get_all_selected_groups(session)

        for group_id in groups:
            await GroupLesson.clear_group_schedule(session, group_id)
            await add_group_schedule(group_id, db)

            logging.info(f'Update schedule for group {group_id} done')
