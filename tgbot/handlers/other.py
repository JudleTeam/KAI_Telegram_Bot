from aiogram import Dispatcher
from aiogram.types import CallbackQuery

from tgbot.misc import callbacks


async def show_pass(call: CallbackQuery):
    await call.answer('In developing!', show_alert=True)


def register_other(dp: Dispatcher):
    dp.register_callback_query_handler(show_pass, text='pass')
