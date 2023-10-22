from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from tgbot.misc.texts import reply_commands
from aiogram.utils.i18n import gettext as _


def get_main_keyboard():
    builder = ReplyKeyboardBuilder()

    builder.button(text=reply_commands.schedule_symbol + _(reply_commands.schedule))
    builder.button(text=reply_commands.education_symbol + _(reply_commands.education))
    builder.button(text=reply_commands.shop_symbol + _(reply_commands.shop))
    builder.button(text=reply_commands.profile_symbol + _(reply_commands.profile))
    builder.button(text=reply_commands.help_symbol + _(reply_commands.help))

    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


def get_send_phone_keyboard():
    builder = ReplyKeyboardBuilder()

    builder.button(text=_(reply_commands.share_contact), request_contact=True)

    return builder.as_markup(resize_keyboard=True)
