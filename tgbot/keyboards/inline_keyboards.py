from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import datetime
from tgbot.misc import callbacks
from tgbot.misc.texts import buttons, roles
from tgbot.services.database.models import Language, User


def get_profile_keyboard(_):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(_(buttons.choose_group), callback_data=callbacks.navigation.new('grp_choose', payload='')),
        InlineKeyboardButton(_(buttons.choose_language),
                             callback_data=callbacks.navigation.new('lang_choose', payload='profile')),
        InlineKeyboardButton(_(buttons.verification), callback_data=callbacks.navigation.new('verification', payload=''))
    )

    return keyboard


def get_group_choose_keyboard(_, user: User, back_to: str, payload: str):
    keyboard = InlineKeyboardMarkup(row_width=3)

    if user.group:
        if user.group in user.selected_groups:
            keyboard.add(
                InlineKeyboardButton(_(buttons.remove_favorite),
                                     callback_data=callbacks.group_choose.new(id=user.group.group_id, action='remove', payload=payload))
            )
        else:
            keyboard.add(
                InlineKeyboardButton(_(buttons.add_favorite),
                                     callback_data=callbacks.group_choose.new(id=user.group.group_id, action='add', payload=payload))
            )

    k_buttons = list()
    for group in user.selected_groups:
        btn_text = f'● {group.group_name} ●' if user.group_id == group.group_id else group.group_name
        k_buttons.append(
            InlineKeyboardButton(btn_text, callback_data=callbacks.group_choose.new(id=group.group_id, action='select', payload=payload))
        )
    keyboard.add(*k_buttons)

    if payload == '':
        keyboard.add(
            InlineKeyboardButton(_(buttons.back), callback_data=callbacks.navigation.new(to=back_to, payload='back_gc'))
        )
    elif payload == 'full_schedule':
        keyboard.add(
            InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='full_schedule', payload=''))
        )
    elif payload == 'main_schedule':
        keyboard.add(
            InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='main_menu', payload=''))
        )
    elif payload == 'at_start':
        keyboard.add(
            InlineKeyboardButton(_(buttons.next_), callback_data=callbacks.navigation.new(to='main_menu', payload=payload))
        )
    else:
        keyboard.add(
            InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='show_day', payload=payload))
        )

    return keyboard


def get_language_choose_keyboard(_, languages: list[Language], at_start=False):
    keyboard = InlineKeyboardMarkup(row_width=1)

    payload = 'at_start' if at_start else ''
    k_buttons = []
    for language in languages:
        callback = callbacks.language_choose.new(lang_id=language.id, code=language.code, payload=payload)
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


def get_main_schedule_keyboard(_, group_name):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(_(buttons.today), callback_data=callbacks.schedule.new(action='show_day', payload=(datetime.datetime.now()).date())),
    )
    keyboard.row(
        InlineKeyboardButton(_(buttons.tomorrow), callback_data=callbacks.schedule.new(action='show_day', payload=(datetime.datetime.now() + datetime.timedelta(days=1)).date())),
        InlineKeyboardButton(_(buttons.day_after_tomorrow), callback_data=callbacks.schedule.new(action='show_day', payload=(datetime.datetime.now() + datetime.timedelta(days=2)).date())),
    )
    keyboard.add(
        InlineKeyboardButton(_(buttons.full_schedule), callback_data=callbacks.schedule.new(action='full_schedule', payload='')),
        InlineKeyboardButton(_(buttons.teachers), callback_data=callbacks.schedule.new(action='teachers', payload='')),
        # InlineKeyboardButton(_(buttons.exams), callback_data='pass'),
        InlineKeyboardButton(_(buttons.group).format(group_name=group_name), callback_data=callbacks.navigation.new(to='grp_choose', payload='main_schedule'))
    )

    return keyboard


def get_schedule_day_keyboard(_, parity, today, group_name):
    keyboard = InlineKeyboardMarkup(row_width=1)

    if parity == 1:
        week_button = buttons.odd_week
    else:
        week_button = buttons.even_week
    keyboard.add(
        InlineKeyboardButton(_(week_button), callback_data=callbacks.change_schedule_week.new(action='day', payload=parity))
    )
    if today.date() != datetime.datetime.today().date():
        keyboard.add(
            InlineKeyboardButton(_(buttons.today), callback_data=callbacks.schedule.new(action='show_day', payload=datetime.datetime.today().date()))
        )
    keyboard.row(
        InlineKeyboardButton(_(buttons.prev_day), callback_data=callbacks.schedule.new(action='show_day', payload=(today - datetime.timedelta(days=1)).date())),
        InlineKeyboardButton(_(buttons.next_day), callback_data=callbacks.schedule.new(action='show_day', payload=(today + datetime.timedelta(days=1)).date()))
    )
    keyboard.add(
        InlineKeyboardButton(_(buttons.group).format(group_name=group_name), callback_data=callbacks.navigation.new(to='grp_choose', payload=today.date())),
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='main_menu', payload=''))
    )

    return keyboard


def get_full_schedule_keyboard(_, parity, group_name):
    keyboard = InlineKeyboardMarkup(row_width=1)

    if parity == 1:
        week_button = buttons.odd_week
    else:
        week_button = buttons.even_week
    keyboard.add(
        InlineKeyboardButton(_(week_button), callback_data=callbacks.change_schedule_week.new(action='week', payload=parity)),
        InlineKeyboardButton(_(buttons.group).format(group_name=group_name), callback_data=callbacks.navigation.new(to='grp_choose', payload='full_schedule')),
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='main_menu', payload=''))
    )
    return keyboard


def get_teachers_keyboard(_):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='main_menu', payload=''))
    )
    return keyboard


def get_verification_keyboard(_, user: User):
    keyboard = InlineKeyboardMarkup()

    if not user.phone:
        keyboard.add(
            InlineKeyboardButton(_(buttons.via_phone), callback_data=callbacks.navigation.new('send_phone', payload=''))
        )

    if not (user.kai_user and user.kai_user.login):
        keyboard.add(
            InlineKeyboardButton(_(buttons.kai_login), callback_data=callbacks.navigation.new('start_login', payload=''))
        )
    else:
        keyboard.add(
            InlineKeyboardButton(_(buttons.kai_logout), callback_data=callbacks.navigation.new('logout', payload=''))
        )

    if user.has_role(roles.verified):
        keyboard.add(
            InlineKeyboardButton(_(buttons.unlink_account), callback_data=callbacks.navigation.new('unlink', payload=''))
        )

    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.navigation.new('profile', payload='back'))
    )

    return keyboard


def get_cancel_keyboard(_, to: str, payload=''):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_(buttons.cancel), callback_data=callbacks.cancel.new(to=to, payload=payload))
    )

    return keyboard


def get_back_keyboard(_, to: str, payload=''):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.navigation.new(to=to, payload=payload))
    )

    return keyboard


def get_channel_keyboard(_, link):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_(buttons.channel), url=link)
    )

    return keyboard


def get_education_keyboard(_):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_(buttons.my_group), callback_data=callbacks.navigation.new(to='my_group', payload=''))
    )

    return keyboard


def get_my_group_keyboard(_, user: User):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(_(buttons.classmates), callback_data=callbacks.navigation.new(to='classmates', payload=''))
    )

    if user.kai_user.is_leader:
        keyboard.add(
            InlineKeyboardButton(_(buttons.edit_pinned_text), callback_data=callbacks.navigation.new(to='edit_pin_text', payload=''))
        )

    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.navigation.new(to='education', payload=''))
    )

    return keyboard
