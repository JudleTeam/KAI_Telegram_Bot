import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _, I18n, FSMI18nMiddleware
from iso_language_codes import language_dictionary

from tgbot.handlers.profile import show_verification
from tgbot.keyboards import inline_keyboards, reply_keyboards
from tgbot.misc.callbacks import Language as LangCallback, Navigation
from tgbot.misc.texts import messages

router = Router()


@router.callback_query(Navigation.filter(F.to == Navigation.To.language_choose))
async def show_language_choose(call: CallbackQuery, callback_data: Navigation, i18n: I18n):
    at_start = callback_data.payload == 'start'

    iso_languages = language_dictionary()
    languages = {locale:iso_languages[locale]['Autonym'] for locale in i18n.available_locales}
    keyboard = inline_keyboards.get_language_choose_keyboard(languages, at_start=at_start)

    await call.message.edit_text(_(messages.language_choose), reply_markup=keyboard)
    await call.answer()


@router.callback_query(LangCallback.filter())
async def choose_language(call: CallbackQuery, callback_data: LangCallback, state: FSMContext,
                          i18n_middleware: FSMI18nMiddleware):
    await i18n_middleware.set_locale(state, callback_data.code)
    logging.info(f'[{call.from_user.id}]: Changed language to {callback_data.code}')

    await call.answer(_(messages.language_changed))
    if callback_data.payload == 'at_start':
        await show_verification(call, callback_data, state)
        return

    await call.message.delete()
    await call.message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard())
