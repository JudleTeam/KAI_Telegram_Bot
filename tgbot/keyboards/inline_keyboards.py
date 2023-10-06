import calendar

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import datetime
from tgbot.misc import callbacks
from tgbot.misc.texts import buttons, roles, rights
from tgbot.services.database.models import Language, User, Group, GroupLesson, Homework


def get_profile_keyboard(_):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(_(buttons.choose_group), callback_data=callbacks.navigation.new('grp_choose', payload='')),
        InlineKeyboardButton(_(buttons.choose_language),
                             callback_data=callbacks.navigation.new('lang_choose', payload='profile')),
        InlineKeyboardButton(_(buttons.verification), callback_data=callbacks.navigation.new('verification', payload='')),
        InlineKeyboardButton(_(buttons.settings), callback_data=callbacks.navigation.new('settings', payload=''))
    )

    return keyboard


def get_settings_keyboard(_, tg_user: User):
    keyboard = InlineKeyboardMarkup(row_width=1)

    if tg_user.use_emoji:
        keyboard.add(
            InlineKeyboardButton(_(buttons.disable_emoji), callback_data=callbacks.settings.new('emoji'))
        )
    else:
        keyboard.add(
            InlineKeyboardButton(_(buttons.enable_emoji), callback_data=callbacks.settings.new('emoji'))
        )

    if tg_user.show_teachers_in_schedule:
        keyboard.add(
            InlineKeyboardButton(_(buttons.disable_teachers), callback_data=callbacks.settings.new('teachers'))
        )
    else:
        keyboard.add(
            InlineKeyboardButton(_(buttons.enable_teachers), callback_data=callbacks.settings.new('teachers'))
        )

    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.navigation.new('profile', payload='settings'))
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
    elif 'day_schedule' in payload:
        payload = payload.split(';')[-1]
        keyboard.add(
            InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='show_day', payload=payload))
        )
    elif 'week_schedule' in payload:
        payload = payload.split(';')[-1]
        keyboard.add(
            InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='week_schedule', payload=payload))
        )
    elif 'full_schedule' in payload:
        parity = payload.split(';')[-1]
        keyboard.add(
            InlineKeyboardButton(_(buttons.back), callback_data=callbacks.full_schedule.new(parity=parity))
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
        InlineKeyboardButton(_(buttons.choose_language), callback_data=callbacks.navigation.new(to='lang_choose', payload='start'))
    )

    return keyboard


def get_main_schedule_keyboard(_, group_name):
    keyboard = InlineKeyboardMarkup(row_width=1)

    now = datetime.datetime.now()

    keyboard.add(
        InlineKeyboardButton(_(buttons.today), callback_data=callbacks.schedule.new(action='show_day', payload='today')),
    )
    keyboard.row(
        InlineKeyboardButton(_(buttons.tomorrow), callback_data=callbacks.schedule.new(action='show_day', payload='tomorrow')),
        InlineKeyboardButton(_(buttons.day_after_tomorrow), callback_data=callbacks.schedule.new(action='show_day', payload='after_tomorrow')),
    )
    keyboard.row(
        InlineKeyboardButton(_(buttons.week_schedule), callback_data=callbacks.schedule.new(action='week_schedule', payload=now.date())),
        InlineKeyboardButton(_(buttons.full_schedule), callback_data=callbacks.full_schedule.new(parity='0'))
    )

    keyboard.add(
        InlineKeyboardButton(_(buttons.group).format(group_name=group_name), callback_data=callbacks.navigation.new(to='grp_choose', payload='main_schedule'))
    )

    return keyboard


def get_full_schedule_keyboard(_, parity: int, group_name):
    keyboard = InlineKeyboardMarkup(row_width=1)

    even = _(buttons.even_week)
    odd = _(buttons.odd_week)
    any_week = _(buttons.any_week)

    if int(parity) == 1:
        odd = '> ' + odd
    elif int(parity) == 2:
        even = '> ' + even
    else:
        any_week = '> ' + any_week

    keyboard.row(
        InlineKeyboardButton(even, callback_data=callbacks.full_schedule.new(parity='2')),
        InlineKeyboardButton(odd, callback_data=callbacks.full_schedule.new(parity='1')),
    )

    keyboard.add(
        InlineKeyboardButton(any_week, callback_data=callbacks.full_schedule.new(parity='0'))
    )

    keyboard.add(
        InlineKeyboardButton(_(buttons.group).format(group_name=group_name), callback_data=callbacks.navigation.new(to='grp_choose', payload=f'full_schedule;{parity}'))
    )

    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='main_menu', payload=''))
    )

    return keyboard


def get_schedule_day_keyboard(_, today, group_name):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(_(buttons.today), callback_data=callbacks.schedule.new(action='show_day', payload='today'))
    )

    keyboard.row(
        InlineKeyboardButton(_(buttons.prev_week), callback_data=callbacks.schedule.new(action='show_day', payload=((today - datetime.timedelta(days=7)).date()))),
        InlineKeyboardButton(_(buttons.prev_day), callback_data=callbacks.schedule.new(action='show_day', payload=(today - datetime.timedelta(days=1)).date())),
        InlineKeyboardButton(_(buttons.next_day), callback_data=callbacks.schedule.new(action='show_day', payload=(today + datetime.timedelta(days=1)).date())),
        InlineKeyboardButton(_(buttons.next_week), callback_data=callbacks.schedule.new(action='show_day', payload=(today + datetime.timedelta(days=7)).date()))
    )

    keyboard.row(
        InlineKeyboardButton(_(buttons.details), callback_data=callbacks.schedule.new(action='day_details', payload=today.date())),
        InlineKeyboardButton(_(buttons.group).format(group_name=group_name), callback_data=callbacks.navigation.new(to='grp_choose', payload=f'day_schedule;{today.date()}'))
    )

    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='main_menu', payload=''))
    )

    return keyboard


def get_day_details_keyboard(_, lessons: list[GroupLesson], date: datetime.date, edit_homework_right: bool):
    keyboard = InlineKeyboardMarkup(row_width=1)

    if edit_homework_right:
        for lesson in lessons:
            btn_text = f'{lesson.start_time.strftime("%H:%M")} | {lesson.discipline.name}'
            keyboard.add(
                InlineKeyboardButton(btn_text, callback_data=callbacks.details.new(action='show', lesson_id=lesson.id, date=date, payload='day_details'))
            )

    prev_week = date - datetime.timedelta(days=7)
    prev_day = date - datetime.timedelta(days=1)
    next_day = date + datetime.timedelta(days=1)
    next_week = date + datetime.timedelta(days=7)
    keyboard.row(
        InlineKeyboardButton(_(buttons.prev_week), callback_data=callbacks.schedule.new(action='day_details', payload=prev_week)),
        InlineKeyboardButton(_(buttons.prev_day), callback_data=callbacks.schedule.new(action='day_details', payload=prev_day)),
        InlineKeyboardButton(_(buttons.next_day), callback_data=callbacks.schedule.new(action='day_details', payload=next_day)),
        InlineKeyboardButton(_(buttons.next_week), callback_data=callbacks.schedule.new(action='day_details', payload=next_week))
    )

    keyboard.add(
        InlineKeyboardButton(_(buttons.schedule), callback_data=callbacks.schedule.new(action='show_day', payload=date))
    )

    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='main_menu', payload=''))
    )

    return keyboard


def get_week_details_keyboard(_, lessons: list[GroupLesson], dates: list[datetime.date], edit_homework_right: bool):
    keyboard = InlineKeyboardMarkup(row_width=3)

    if edit_homework_right:
        keyboard_buttons = list()
        for lesson, date in zip(lessons, dates):
            btn_text = f'{_(calendar.day_name[date.weekday()])[:2]} | {lesson.start_time.strftime("%H:%M")}'
            keyboard_buttons.append(
                InlineKeyboardButton(btn_text, callback_data=callbacks.details.new(action='show', lesson_id=lesson.id, date=date, payload='week_details'))
            )

        keyboard.add(*keyboard_buttons)

    date = dates[0]

    int_parity = 2 if not int(date.strftime('%V')) % 2 else 1
    if int_parity == 1:
        keyboard.add(
            InlineKeyboardButton(_(buttons.odd_week), callback_data='pass')
        )
    else:
        keyboard.add(
            InlineKeyboardButton(_(buttons.even_week), callback_data='pass')
        )

    next_week = date + datetime.timedelta(weeks=1)
    prev_week = date - datetime.timedelta(weeks=1)
    keyboard.row(
        InlineKeyboardButton(_(buttons.prev_week), callback_data=callbacks.schedule.new(action='week_details', payload=prev_week)),
        InlineKeyboardButton(_(buttons.next_week), callback_data=callbacks.schedule.new(action='week_details', payload=next_week))
    )

    keyboard.add(
        InlineKeyboardButton(_(buttons.schedule), callback_data=callbacks.schedule.new(action='week_schedule', payload=date))
    )

    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action='main_menu', payload=''))
    )

    return keyboard


def get_homework_keyboard(_, lesson_id: int, date: datetime.date, homework: Homework | None, payload: str):
    keyboard = InlineKeyboardMarkup(row_width=1)

    if homework is None:
        keyboard.add(
            InlineKeyboardButton(_(buttons.add), callback_data=callbacks.details.new(action='add', lesson_id=lesson_id, date=date, payload=payload))
        )
    else:
        keyboard.add(
            InlineKeyboardButton(_(buttons.edit), callback_data=callbacks.details.new(action='edit', lesson_id=lesson_id, date=date, payload=payload)),
            InlineKeyboardButton(_(buttons.delete), callback_data=callbacks.details.new(action='delete', lesson_id=lesson_id, date=date, payload=payload))
        )

    keyboard.add(
        InlineKeyboardButton(_(buttons.back), callback_data=callbacks.schedule.new(action=payload, payload=date))
    )

    return keyboard


def get_week_schedule_keyboard(_, today: datetime.datetime, group_name):
    keyboard = InlineKeyboardMarkup(row_width=1)

    int_parity = 2 if not int(today.strftime('%V')) % 2 else 1

    next_week = today + datetime.timedelta(weeks=1)
    prev_week = today - datetime.timedelta(weeks=1)

    if int_parity == 1:
        keyboard.add(
            InlineKeyboardButton(_(buttons.odd_week), callback_data='pass')
        )
    else:
        keyboard.add(
            InlineKeyboardButton(_(buttons.even_week), callback_data='pass')
        )

    keyboard.row(
        InlineKeyboardButton(_(buttons.prev_week), callback_data=callbacks.schedule.new(action='week_schedule', payload=prev_week.date())),
        InlineKeyboardButton(_(buttons.next_week), callback_data=callbacks.schedule.new(action='week_schedule', payload=next_week.date()))
    )

    keyboard.row(
        InlineKeyboardButton(_(buttons.details), callback_data=callbacks.schedule.new(action='week_details', payload=today.date())),
        InlineKeyboardButton(_(buttons.group).format(group_name=group_name), callback_data=callbacks.navigation.new(to='grp_choose', payload=f'week_schedule;{today.date()}'))
    )

    keyboard.add(
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
    # else:
    #     keyboard.add(
    #         InlineKeyboardButton(_(buttons.kai_logout), callback_data=callbacks.action.new('logout', payload))
    #     )

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
        InlineKeyboardButton(_(buttons.clear), callback_data=callbacks.action.new(name='clear_pin_text', payload='')),
        InlineKeyboardButton(_(buttons.cancel), callback_data=callbacks.cancel.new(to='my_group', payload=''))
    )

    return keyboard


def get_help_keyboard(_, contact_url, channel_url, donate_url, guide_link):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.row(
        InlineKeyboardButton(_(buttons.contact_us), url=contact_url),
        InlineKeyboardButton(_(buttons.channel), url=channel_url)
    )

    keyboard.add(InlineKeyboardButton(_(buttons.support_project), url=donate_url))
    keyboard.add(InlineKeyboardButton(_(buttons.guide), url=guide_link))

    return keyboard
