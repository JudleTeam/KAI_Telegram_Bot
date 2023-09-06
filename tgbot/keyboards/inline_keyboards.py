from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import datetime
from tgbot.misc import callbacks
from tgbot.misc.texts import buttons, roles, rights
from tgbot.services.database.models import Language, User, Group


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
        if user.group in user.favorite_groups:
            keyboard.add(
                InlineKeyboardButton(_(buttons.remove_favorite),
                                     callback_data=callbacks.group_choose.new(id=user.group.group_id, action='remove', payload=payload))
            )
        else:
            keyboard.add(
                InlineKeyboardButton(_(buttons.add_favorite),
                                     callback_data=callbacks.group_choose.new(id=user.group.group_id, action='add', payload=payload))
            )

    native_group_name = None
    if user.has_role(roles.verified):
        native_group_name = user.kai_user.group.group_name
        keyboard.add(
            InlineKeyboardButton(f'⭐ {native_group_name} ⭐',
                                 callback_data=callbacks.group_choose.new(id=user.kai_user.group.group_id, action='select', payload=payload))
        )

    k_buttons = list()
    for group in user.favorite_groups:
        if native_group_name == group.group_name:
            continue
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
    elif payload == 'teachers':
        keyboard.add(
            InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='teachers', payload=''))
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
        InlineKeyboardButton(_(week_button), callback_data=callbacks.change_schedule_week.new(action='day', payload=today.date()))
    )

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


def get_teachers_keyboard(_, group_name):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(_(buttons.group).format(group_name=group_name),
                             callback_data=callbacks.navigation.new(to='grp_choose', payload='teachers')),
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.navigation.new('education', payload=''))
    )
    return keyboard


def get_verification_keyboard(_, user: User, payload):
    keyboard = InlineKeyboardMarkup()

    is_verified = user.has_role(roles.verified)

    if not user.phone:
        keyboard.add(
            InlineKeyboardButton(_(buttons.via_phone), callback_data=callbacks.action.new('send_phone', payload))
        )
    elif not is_verified:
        keyboard.add(
            InlineKeyboardButton(_(buttons.check_phone), callback_data=callbacks.action.new('check_phone', payload))
        )

    if not (user.has_role(roles.authorized)):
        keyboard.add(
            InlineKeyboardButton(_(buttons.kai_login), callback_data=callbacks.action.new('start_login', payload))
        )
    else:
        keyboard.add(
            InlineKeyboardButton(_(buttons.kai_logout), callback_data=callbacks.action.new('logout', payload))
        )

    if is_verified:
        keyboard.add(
            InlineKeyboardButton(_(buttons.unlink_account), callback_data=callbacks.action.new('unlink', payload))
        )

    if payload == 'at_start':
        keyboard.add(
            InlineKeyboardButton(_(buttons.next_), callback_data=callbacks.navigation.new('grp_choose', payload))
        )
    else:
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
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(_(buttons.my_group), callback_data=callbacks.navigation.new(to='my_group', payload='')),
        InlineKeyboardButton(_(buttons.teachers), callback_data=callbacks.schedule.new(action='teachers', payload=''))
    )

    return keyboard


def get_my_group_keyboard(_, user: User):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(_(buttons.classmates), callback_data=callbacks.navigation.new(to='classmates', payload='')),
        InlineKeyboardButton(_(buttons.homework), callback_data='pass'),
        InlineKeyboardButton(_(buttons.documents), callback_data=callbacks.navigation.new(to='documents', payload=''))
    )

    if user.has_right_to(rights.edit_group_pinned_message):
        keyboard.add(
            InlineKeyboardButton(_(buttons.edit_pinned_text), callback_data=callbacks.navigation.new(to='edit_pin_text', payload=''))
        )

    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.navigation.new(to='education', payload=''))
    )

    return keyboard


def get_documents_keyboard(_):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(_(buttons.educational_program), callback_data=callbacks.action.new('doc', 'program')),
        InlineKeyboardButton(_(buttons.syllabus), callback_data=callbacks.action.new('doc', 'syllabus')),
        InlineKeyboardButton(_(buttons.study_schedule), callback_data=callbacks.action.new('doc', 'schedule')),
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.navigation.new(to='my_group', payload=''))
    )

    return keyboard


def get_pin_text_keyboard(_):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(_(buttons.clear), callback_data=callbacks.action.new(to='clear_pin_text', payload='')),
        InlineKeyboardButton(_(buttons.cancel), callback_data=callbacks.cancel.new(to='my_group', payload=''))
    )

    return keyboard


def get_help_keyboard(_, contact_url):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(_(buttons.contact_us), url=contact_url)
    )

    return keyboard
