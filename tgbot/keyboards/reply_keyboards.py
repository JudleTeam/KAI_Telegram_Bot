from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from tgbot.misc.texts import reply_commands


def get_main_keyboard(_):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    keyboard.add(
        KeyboardButton(reply_commands.schedule_symbol + _(reply_commands.schedule)),
        KeyboardButton(reply_commands.education_symbol + _(reply_commands.education)),
        KeyboardButton(reply_commands.shop_symbol + _(reply_commands.shop)),
        KeyboardButton(reply_commands.profile_symbol + _(reply_commands.profile))
    )

    return keyboard


def get_send_phone_keyboard(_):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add(
        KeyboardButton(_(reply_commands.share_contact), request_contact=True)
    )

    return keyboard
