import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.handlers.profile import show_verification
from tgbot.keyboards import inline_keyboards, reply_keyboards
from tgbot.misc.callbacks import Language as LangCallback, Navigation
from tgbot.misc.texts import messages
from tgbot.services.database.models import Language, User

router = Router()


@router.callback_query(Navigation.filter(F.to == Navigation.To.language_choose))
async def show_language_choose(call: CallbackQuery, callback_data: Navigation, _, db: async_sessionmaker):
    available_languages = await Language.get_available_languages(db)

    at_start = callback_data.payload == 'start'
    keyboard = inline_keyboards.get_language_choose_keyboard(_, available_languages, at_start=at_start)
    await call.message.edit_text(_(messages.language_choose), reply_markup=keyboard)
    await call.answer()


@router.callback_query(LangCallback.filter())
async def choose_language(call: CallbackQuery, callback_data: LangCallback, state: FSMContext, _, db: async_sessionmaker,
                          redis: Redis):
    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        user.language_id = callback_data.lang_id

    await redis.set(name=f'{user.telegram_id}:lang', value=callback_data.code)
    _.ctx_locale.set(callback_data.code)

    logging.info(f'[{call.from_user.id}]: Changed language to {callback_data.code}')

    await call.answer(_(messages.language_changed))
    if callback_data.payload == 'at_start':
        await show_verification(call, callback_data, state)
        return

    await call.message.delete()
    await call.message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard(_))
