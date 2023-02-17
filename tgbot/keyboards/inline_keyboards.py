from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.misc import callbacks, messages
from tgbot.services.database.models import Language


def get_language_choose_keyboard(_, languages: list[Language], at_start=False):
    keyboard = InlineKeyboardMarkup(row_width=1)

    buttons = []
    for language in languages:
        callback = callbacks.language_choose.new(lang_id=language.id, code=language.code)
        buttons.append(
            InlineKeyboardButton(language.title, callback_data=callback)
        )
    keyboard.add(*buttons)

    if not at_start:
        keyboard.add(
            InlineKeyboardButton(_(messages.back_button), callback_data='pass')
        )

    return keyboard


def get_start_keyboard(_):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_(messages.choose_language_button),
                             callback_data=callbacks.navigation.new(to='lang_choose', payload='start'))
    )

    return keyboard
