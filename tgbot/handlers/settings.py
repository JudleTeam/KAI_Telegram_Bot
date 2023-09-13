from aiogram import Dispatcher
from aiogram.types import CallbackQuery

from tgbot.handlers.profile import show_settings
from tgbot.misc import callbacks
from tgbot.services.database.models import User


async def switch_use_emoji(call: CallbackQuery):
    db = call.bot.get('database')

    async with db.begin() as session:
        tg_user: User = await session.get(User, call.from_user.id)
        tg_user.use_emoji = not tg_user.use_emoji

    await show_settings(call)


async def switch_show_teachers(call: CallbackQuery):
    db = call.bot.get('database')

    async with db.begin() as session:
        tg_user: User = await session.get(User, call.from_user.id)
        tg_user.show_teachers_in_schedule = not tg_user.show_teachers_in_schedule

    await show_settings(call)


def register_settings(dp: Dispatcher):
    dp.register_callback_query_handler(switch_use_emoji, callbacks.settings.filter(action='emoji'))
    dp.register_callback_query_handler(switch_show_teachers, callbacks.settings.filter(action='teachers'))
