import datetime
import logging
import time

from aiogram import Bot
from sqlalchemy import select, text, delete
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.services.database.models import User, GroupLesson
from tgbot.services.kai_parser.utils import parse_all_groups_schedule


async def update_schedule(bot: Bot, db: AsyncSession):
    await parse_all_groups_schedule(db)
