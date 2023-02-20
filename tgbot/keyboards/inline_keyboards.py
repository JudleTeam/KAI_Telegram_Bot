from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import datetime
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


def get_main_schedule_keyboard(_):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(_(buttons.today), callback_data=callbacks.schedule.new(action='show_day', payload=(datetime.datetime.now()).date())),
        InlineKeyboardButton(_(buttons.tomorrow), callback_data=callbacks.schedule.new(action='show_day', payload=(datetime.datetime.now() + datetime.timedelta(days=1)).date())),
        InlineKeyboardButton(_(buttons.day_after_tomorrow), callback_data=callbacks.schedule.new(action='show_day', payload=(datetime.datetime.now() + datetime.timedelta(days=2)).date())),
        InlineKeyboardButton(_(buttons.full_schedule), callback_data=callbacks.schedule.new(action='full_schedule', payload='')),
        InlineKeyboardButton(_(buttons.teachers), callback_data=callbacks.schedule.new(action='teachers', payload='')),
        InlineKeyboardButton(_(buttons.exams), callback_data=callbacks.schedule.new(action='exams', payload=''))
    )

    return keyboard


def get_schedule_day_keyboard(_, parity, today):
    keyboard = InlineKeyboardMarkup()

    if parity == 1:
        week_button = buttons.odd_week
    else:
        week_button = buttons.even_week
    keyboard.add(
        InlineKeyboardButton(_(week_button), callback_data=callbacks.change_schedule_week.new(action='day', payload=parity))
    )
    keyboard.add(
        InlineKeyboardButton(_(buttons.prev_day), callback_data=callbacks.schedule.new(action='show_day', payload=(today - datetime.timedelta(days=1)).date())),
        InlineKeyboardButton(_(buttons.next_day), callback_data=callbacks.schedule.new(action='show_day', payload=(today + datetime.timedelta(days=1)).date()))
    )
    keyboard.add(
        InlineKeyboardButton(_(buttons.group), callback_data=callbacks.schedule.new(action='change_group', payload=''))
    )
    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='main_menu', payload=''))
    )

    return keyboard


def get_full_schedule_keyboard(_, parity):
    keyboard = InlineKeyboardMarkup(row_width=1)

    if parity == 1:
        week_button = buttons.odd_week
    else:
        week_button = buttons.even_week
    keyboard.add(
        InlineKeyboardButton(_(week_button), callback_data=callbacks.change_schedule_week.new(action='week', payload=parity)),
        InlineKeyboardButton(_(buttons.group), callback_data=callbacks.schedule.new(action='change_group', payload='')),
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='main_menu', payload=''))
    )
    return keyboard


def get_teachers_keyboard(_):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='main_menu', payload=''))
    )
    return keyboard
