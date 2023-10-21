from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.handlers.profile import show_settings
from tgbot.misc.callbacks import Settings
from tgbot.services.database.models import User

router = Router()


@router.callback_query(Settings.filter(F.action == Settings.Action.emoji))
async def switch_use_emoji(call: CallbackQuery, db: async_sessionmaker):
    async with db.begin() as session:
        tg_user = await session.get(User, call.from_user.id)
        tg_user.use_emoji = not tg_user.use_emoji

    await show_settings(call)


@router.callback_query(Settings.filter(F.action == Settings.Action.teachers))
async def switch_show_teachers(call: CallbackQuery, db: async_sessionmaker):
    async with db.begin() as session:
        tg_user = await session.get(User, call.from_user.id)
        tg_user.show_teachers_in_schedule = not tg_user.show_teachers_in_schedule

    await show_settings(call)
