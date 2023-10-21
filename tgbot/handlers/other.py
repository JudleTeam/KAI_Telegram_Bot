import logging

from aiogram import Dispatcher, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from tgbot.handlers.details import show_lesson_menu
from tgbot.handlers.education import show_my_group
from tgbot.handlers.main_menu import show_profile_menu
from tgbot.handlers.profile import show_verification
from tgbot.misc import callbacks
from tgbot.misc.callbacks import Cancel
from tgbot.misc.texts import messages

router = Router()


@router.callback_query(F.text == 'dev')
async def show_dev(call: CallbackQuery, _):
    await call.answer(_(messages.in_development), show_alert=True)


@router.callback_query(F.text == 'pass')
async def show_pass(call: CallbackQuery):
    await call.answer()


@router.callback_query(Cancel.filter())
async def cancel(call: CallbackQuery, callback_data: Cancel, state: FSMContext):
    await state.clear()
    await call.answer()

    match callback_data.to:
        case 'profile': await show_profile_menu(call, callback_data, state)
        case 'verification':
            logging.info(f'[{call.from_user.id}]: Cancel KAI login')
            await show_verification(call, callback_data, state)
        case 'my_group': await show_my_group(call)
        case 'homework':
            lesson_id, date, payload = callback_data.payload.split(';')
            await show_lesson_menu(call, {'lesson_id': lesson_id, 'date': date, 'payload': payload})
