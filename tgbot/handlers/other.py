import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.handlers.details import show_lesson_menu
from tgbot.handlers.education import show_my_group
from tgbot.handlers.main_menu import show_profile_menu
from tgbot.handlers.profile import show_verification
from tgbot.misc.callbacks import Cancel, Details
from tgbot.misc.texts import messages

router = Router()


@router.callback_query(F.data == 'dev')
async def show_dev(call: CallbackQuery):
    await call.answer(_(messages.in_development), show_alert=True)


@router.callback_query(F.data == 'pass')
async def show_pass(call: CallbackQuery):
    await call.answer(_(messages.empty_button))


@router.callback_query(Cancel.filter())
async def cancel(call: CallbackQuery, callback_data: Cancel, state: FSMContext, db: async_sessionmaker, bot: Bot):
    await state.clear()
    await call.answer()

    match callback_data.to:
        case Cancel.To.profile: await show_profile_menu(call, callback_data, state)
        case Cancel.To.verification:
            logging.info(f'[{call.from_user.id}]: Cancel KAI login')
            await show_verification(call, callback_data, state, db)
        case Cancel.To.my_group: await show_my_group(call, db)
        case Cancel.To.homework:
            lesson_id, date, payload = callback_data.payload.split(';')
            callback = Details(action=Details.Action.show, lesson_id=lesson_id, date=date, payload=payload)
            await show_lesson_menu(call, callback, db, bot)
