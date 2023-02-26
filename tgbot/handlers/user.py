from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery

from tgbot.handlers.main_menu import show_profile_menu
from tgbot.handlers.profile import show_group_choose
from tgbot.keyboards import inline_keyboards, reply_keyboards
from tgbot.misc import callbacks
from tgbot.misc.texts import messages
from tgbot.services.database.models import Language, User


async def show_language_choose(call: CallbackQuery, callback_data: dict):
    _ = call.bot.get('_')
    db_session = call.bot.get('database')

    available_languages = await Language.get_available_languages(db_session)

    at_start = callback_data['payload'] == 'start'
    keyboard = inline_keyboards.get_language_choose_keyboard(_, available_languages, at_start=at_start)
    await call.message.edit_text(_(messages.language_choose), reply_markup=keyboard)
    await call.answer()


async def choose_language(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    redis = call.bot.get('redis')
    db_session = call.bot.get('database')

    async with db_session.begin() as session:
        user = await session.get(User, call.from_user.id)
        user.language_id = int(callback_data['lang_id'])

    await redis.set(name=f'{user.telegram_id}:lang', value=callback_data['code'])
    _.ctx_locale.set(callback_data['code'])

    await call.answer(_(messages.language_changed))
    if callback_data['payload'] == 'at_start':
        await show_group_choose(call, callback_data, state)
        return

    await call.message.delete()
    await call.message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard(_))


async def show_main_menu(call: CallbackQuery):
    _ = call.bot.get('_')
    await call.message.edit_text(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard(_))
    await call.answer()


def register_user(dp: Dispatcher):
    dp.register_callback_query_handler(show_main_menu, callbacks.navigation.filter(to='main_menu'))

    dp.register_callback_query_handler(show_language_choose, callbacks.navigation.filter(to='lang_choose'))
    dp.register_callback_query_handler(choose_language, callbacks.language_choose.filter())
