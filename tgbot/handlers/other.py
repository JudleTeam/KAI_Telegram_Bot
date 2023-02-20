from aiogram import Dispatcher
from aiogram.types import CallbackQuery

from tgbot.misc import callbacks
from tgbot.misc.texts import messages


async def show_pass(call: CallbackQuery):
    _ = call.bot.get('_')
    await call.answer(_(messages.in_development), show_alert=True)


def register_other(dp: Dispatcher):
    dp.register_callback_query_handler(show_pass, text='pass')
