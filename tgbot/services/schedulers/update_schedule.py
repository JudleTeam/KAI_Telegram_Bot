import datetime
import logging
import time

from aiogram import Bot
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.services.database.models import User


async def update_schedule(bot: Bot, db: AsyncSession):
    async with db.begin() as session:
        # get groups to parse
        stm = 'select group_id from selected_group'
        group_ids = (await session.execute(stm)).scalars().all()

    for group_id in group_ids:
        print(group_id)
