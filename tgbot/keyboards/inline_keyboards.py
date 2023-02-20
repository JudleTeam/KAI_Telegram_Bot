from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.misc import callbacks
from tgbot.misc.texts import buttons
from tgbot.services.database.models import Language, User


def get_profile_keyboard(_):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(_(buttons.choose_group), callback_data=callbacks.navigation.new('grp_choose', payload='')),
        InlineKeyboardButton(_(buttons.choose_language),
                             callback_data=callbacks.navigation.new('lang_choose', payload='profile')),
    )

    return keyboard


def get_group_choose_keyboard(_, user: User, back_to: str):
    keyboard = InlineKeyboardMarkup(row_width=3)

    if user.group:
        if user.group in user.selected_groups:
            keyboard.add(
                InlineKeyboardButton(_(buttons.remove_favorite),
                                     callback_data=callbacks.group_choose.new(id=user.group.group_id, action='remove'))
            )
        else:
            keyboard.add(
                InlineKeyboardButton(_(buttons.add_favorite),
                                     callback_data=callbacks.group_choose.new(id=user.group.group_id, action='add'))
            )

    k_buttons = list()
    for group in user.selected_groups:
        k_buttons.append(
            InlineKeyboardButton(group.group_name, callback_data=callbacks.group_choose.new(id=group.group_id, action='select'))
        )
    keyboard.add(*k_buttons)

    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.navigation.new(to=back_to, payload='back_gc'))
    )

    return keyboard


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
            InlineKeyboardButton(_(buttons.back), callback_data=callbacks.navigation.new('profile', payload='back'))
        )

    return keyboard


def get_start_keyboard(_):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_(buttons.choose_language),
                             callback_data=callbacks.navigation.new(to='lang_choose', payload='start'))
    )

    return keyboard
