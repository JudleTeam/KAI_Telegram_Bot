from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.misc import callbacks
from tgbot.misc.texts import buttons
from tgbot.services.database.models import Language


def get_language_choose_keyboard(_, languages: list[Language], at_start=False):
    keyboard = InlineKeyboardMarkup(row_width=1)

    k_buttons = []
    for language in languages:
        callback = callbacks.language_choose.new(lang_id=language.id, code=language.code)
        k_buttons.append(
            InlineKeyboardButton(language.title, callback_data=callback)
        )
    keyboard.add(*k_buttons)

    if not at_start:
        keyboard.add(
            InlineKeyboardButton(_(buttons.back), callback_data='pass')
        )

    return keyboard


def get_start_keyboard(_):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_(buttons.choose_language),
                             callback_data=callbacks.navigation.new(to='lang_choose', payload='start'))
    )

    return keyboard
