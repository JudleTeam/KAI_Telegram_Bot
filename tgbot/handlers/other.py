import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery

from tgbot.handlers.education import show_my_group
from tgbot.handlers.main_menu import show_profile_menu
from tgbot.handlers.profile import show_verification
from tgbot.misc import callbacks
from tgbot.misc.texts import messages


async def show_pass(call: CallbackQuery):
    _ = call.bot.get('_')
    await call.answer(_(messages.in_development), show_alert=True)


async def cancel(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.finish()
    await call.answer()

    match callback_data['to']:
        case 'profile': await show_profile_menu(call, callback_data, state)
        case 'verification':
            logging.info(f'[{call.from_user.id}]: Cancel KAI login')
            await show_verification(call)
        case 'my_group': await show_my_group(call)


def register_other(dp: Dispatcher):
    dp.register_callback_query_handler(show_pass, text='pass')
    dp.register_callback_query_handler(cancel, callbacks.cancel.filter(), state='*')
