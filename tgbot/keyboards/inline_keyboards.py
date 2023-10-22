import calendar

from aiogram.utils.i18n import gettext as _

import datetime
from datetime import timedelta

from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.misc.callbacks import (
    Navigation, Language as LangCallback, Action, Cancel, Schedule, Details, Settings, Group as GroupCallback,
    FullSchedule
)
from tgbot.misc.texts import buttons, roles, rights
from tgbot.services.database.models import User, GroupLesson, Homework


def get_profile_keyboard():
    builder = InlineKeyboardBuilder()

    builder.button(text=_(buttons.choose_group), callback_data=Navigation(to=Navigation.To.group_choose))
    builder.button(text=_(buttons.choose_language), callback_data=Navigation(to=Navigation.To.language_choose))
    builder.button(text=_(buttons.verification), callback_data=Navigation(to=Navigation.To.verification))
    builder.button(text=_(buttons.settings), callback_data=Navigation(to=Navigation.To.settings))

    builder.adjust(1)

    return builder.as_markup()


def get_settings_keyboard(tg_user: User):
    builder = InlineKeyboardBuilder()

    emoji_btn_text = _(buttons.disable_emoji) if tg_user.use_emoji else _(buttons.enable_emoji)
    builder.button(text=emoji_btn_text, callback_data=Settings(action=Settings.Action.emoji))

    teachers_btn_text = _(buttons.disable_teachers) if tg_user.show_teachers_in_schedule else _(buttons.enable_teachers)
    builder.button(text=teachers_btn_text, callback_data=Settings(action=Settings.Action.teachers))

    builder.button(text=_(buttons.back), callback_data=Navigation(to=Navigation.To.profile, payload='settings'))

    builder.adjust(1)

    return builder.as_markup()


def get_group_choose_keyboard(user: User, back_to: Navigation.To, payload: str):
    builder_1 = InlineKeyboardBuilder()

    if user.group:
        if user.group in user.favorite_groups:
            builder_1.button(
                text=_(buttons.remove_favorite),
                callback_data=GroupCallback(action=GroupCallback.Action.remove, id=user.group_id, payload=payload)
            )
        else:
            builder_1.button(
                text=_(buttons.add_favorite),
                callback_data=GroupCallback(action=GroupCallback.Action.add, id=user.group_id, payload=payload)
            )

    native_group_name = None
    if user.has_role(roles.verified):
        native_group_name = user.kai_user.group.group_name
        native_group_btn_text = f'⭐ {native_group_name} ⭐'
        if user.group == user.kai_user.group:
            native_group_btn_text = f'●{native_group_btn_text}●'
        builder_1.button(
            text=native_group_btn_text,
            callback_data=GroupCallback(action=GroupCallback.Action.select, id=user.kai_user.group_id, payload=payload)
        )

    builder_1.adjust(1)

    builder_2 = InlineKeyboardBuilder()
    for group in user.favorite_groups:
        if native_group_name == group.group_name:
            continue
        btn_text = f'● {group.group_name} ●' if user.group == group else str(group.group_name)
        builder_2.button(
            text=btn_text,
            callback_data=GroupCallback(action=GroupCallback.Action.select, id=group.group_id, payload=payload)
        )

    builder_2.adjust(3)

    builder_3 = InlineKeyboardBuilder()

    match payload:
        case None: builder_3.button(text=_(buttons.back), callback_data=Navigation(to=back_to, payload='back_gc'))
        case 'main_schedule':
            builder_3.button(text=_(buttons.back), callback_data=Navigation(to=Navigation.To.schedule_menu))
        case 'at_start':
            builder_3.button(text=_(buttons.back), callback_data=Navigation(to=Navigation.To.main_menu, payload=payload))
        case 'teachers':
            builder_3.button(text=_(buttons.back), callback_data=Navigation(to=Navigation.To.teachers))
        case _ if 'day_schedule' in payload:
            payload = payload.split(';')[-1]
            builder_3.button(text=_(buttons.back),
                             callback_data=Schedule(action=Schedule.Action.show_day, date=payload))
        case _ if 'week_schedule' in payload:
            payload = payload.split(';')[-1]
            builder_3.button(text=_(buttons.back),
                             callback_data=Schedule(action=Schedule.Action.show_week, date=payload))
        case _ if 'full_schedule' in payload:
            parity = int(payload.split(';')[-1])
            builder_3.button(text=_(buttons.back), callback_data=FullSchedule(parity=parity))

    builder_3.adjust(1)

    return builder_1.attach(builder_2).attach(builder_3).as_markup()


def get_language_choose_keyboard(languages: dict[str, str], at_start=False):
    builder = InlineKeyboardBuilder()

    payload = 'at_start' if at_start else ''
    for code, title in languages.items():
        builder.button(text=title, callback_data=LangCallback(code=code, payload=payload))

    if not at_start:
        builder.button(text=_(buttons.back), callback_data=Navigation(to=Navigation.To.profile, payload='back'))

    builder.adjust(1)

    return builder.as_markup()


def get_start_keyboard():
    builder = InlineKeyboardBuilder()

    builder.button(text=_(buttons.choose_language),
                   callback_data=Navigation(to=Navigation.To.language_choose, payload='start'))

    return builder.as_markup()


def get_main_schedule_keyboard(group_name):
    today_iso = datetime.datetime.now().date().isoformat()

    builder = InlineKeyboardBuilder()

    builder.button(text=_(buttons.today), callback_data=Schedule(action=Schedule.Action.show_day, date='today'))

    builder.button(text=_(buttons.tomorrow),
                   callback_data=Schedule(action=Schedule.Action.show_day, date='tomorrow'))
    builder.button(text=_(buttons.day_after_tomorrow),
                   callback_data=Schedule(action=Schedule.Action.show_day, date='after_tomorrow'))

    builder.button(text=_(buttons.week_schedule),
                   callback_data=Schedule(action=Schedule.Action.show_week, date=today_iso))
    builder.button(text=_(buttons.full_schedule), callback_data=FullSchedule(parity=0))

    builder.button(text=_(buttons.group).format(group_name=group_name),
                   callback_data=Navigation(to=Navigation.To.group_choose, payload='main_schedule'))

    builder.adjust(1, 2, 2, 1)

    return builder.as_markup()


def get_full_schedule_keyboard(parity: int, group_name):
    even = _(buttons.even_week)
    odd = _(buttons.odd_week)
    any_week = _(buttons.any_week)

    if int(parity) == 1:
        odd = '> ' + odd
    elif int(parity) == 2:
        even = '> ' + even
    else:
        any_week = '> ' + any_week

    builder = InlineKeyboardBuilder()

    builder.button(text=even, callback_data=FullSchedule(parity=2))
    builder.button(text=odd, callback_data=FullSchedule(parity=1))

    builder.button(text=any_week, callback_data=FullSchedule(parity=0))

    builder.button(
        text=_(buttons.group).format(group_name=group_name),
        callback_data=Navigation(to=Navigation.To.group_choose, payload=f'full_schedule;{parity}')
    )

    builder.button(text=_(buttons.back), callback_data=Navigation(to=Navigation.To.schedule_menu))

    builder.adjust(2, 1)

    return builder.as_markup()


def get_schedule_day_keyboard(today: datetime.date, group_name):
    if isinstance(today, datetime.datetime):
        today = today.date()

    builder = InlineKeyboardBuilder()

    builder.button(text=_(buttons.today), callback_data=Schedule(action=Schedule.Action.show_day, date='today'))

    builder.button(
        text=_(buttons.prev_week),
        callback_data=Schedule(action=Schedule.Action.show_day, date=(today - timedelta(days=7)).isoformat())
    )
    builder.button(
        text=_(buttons.prev_day),
        callback_data=Schedule(action=Schedule.Action.show_day, date=(today - timedelta(days=1)).isoformat())
    )
    builder.button(
        text=_(buttons.next_day),
        callback_data=Schedule(action=Schedule.Action.show_day, date=(today + timedelta(days=1)).isoformat())
    )
    builder.button(
        text=_(buttons.next_week),
        callback_data=Schedule(action=Schedule.Action.show_day, date=(today + timedelta(days=7)).isoformat())
    )

    builder.button(text=_(buttons.details),
                   callback_data=Schedule(action=Schedule.Action.day_details, date=today.isoformat()))
    builder.button(
        text=_(buttons.group).format(group_name=group_name),
        callback_data=Navigation(to=Navigation.To.group_choose, payload=f'day_schedule;{today.isoformat()}')
    )

    builder.button(text=_(buttons.back), callback_data=Navigation(to=Navigation.To.schedule_menu))

    builder.adjust(1, 4, 2, 1)

    return builder.as_markup()


def get_day_details_keyboard(lessons: list[GroupLesson], date: datetime.date, edit_homework_right: bool):
    builder_1 = InlineKeyboardBuilder()

    if edit_homework_right:
        for lesson in lessons:
            btn_text = f'{lesson.start_time.strftime("%H:%M")} | {lesson.discipline.name}'
            builder_1.button(
                text=btn_text,
                callback_data=Details(action=Details.Action.show, lesson_id=lesson.id, date=date.isoformat(), payload=Schedule.Action.day_details)
            )

    builder_1.adjust(1)

    prev_week = date - datetime.timedelta(days=7)
    prev_day = date - datetime.timedelta(days=1)
    next_day = date + datetime.timedelta(days=1)
    next_week = date + datetime.timedelta(days=7)

    builder_2 = InlineKeyboardBuilder()

    builder_2.button(text=_(buttons.prev_week),
                     callback_data=Schedule(action=Schedule.Action.day_details, date=prev_week.isoformat()))
    builder_2.button(text=_(buttons.prev_day),
                     callback_data=Schedule(action=Schedule.Action.day_details, date=prev_day.isoformat()))
    builder_2.button(text=_(buttons.next_day),
                     callback_data=Schedule(action=Schedule.Action.day_details, date=next_day.isoformat()))
    builder_2.button(text=_(buttons.next_week),
                     callback_data=Schedule(action=Schedule.Action.day_details, date=next_week.isoformat()))

    builder_2.button(text=_(buttons.schedule),
                     callback_data=Schedule(action=Schedule.Action.show_day, date=date.isoformat()))
    builder_2.button(text=_(buttons.back), callback_data=Navigation(to=Navigation.To.schedule_menu))

    builder_2.adjust(4, 1)

    return builder_1.attach(builder_2).as_markup()


def get_week_details_keyboard(lessons: list[GroupLesson], dates: list[datetime.date], edit_homework_right: bool):
    builder_1 = InlineKeyboardBuilder()

    if edit_homework_right:
        for lesson, date in zip(lessons, dates):
            btn_text = f'{_(calendar.day_name[date.weekday()])[:2]} | {lesson.start_time.strftime("%H:%M")}'
            builder_1.button(
                text=btn_text,
                callback_data=Details(action=Details.Action.show, lesson_id=lesson.id, date=date.isoformat(), payload=Schedule.Action.week_details)
            )

    builder_1.adjust(3)

    builder_2 = InlineKeyboardBuilder()
    date = dates[0]
    int_parity = 2 if not int(date.strftime('%V')) % 2 else 1
    parity_text = _(buttons.odd_week) if int_parity == 1 else _(buttons.even_week)
    builder_2.button(text=parity_text, callback_data='pass')

    next_week = date + datetime.timedelta(weeks=1)
    prev_week = date - datetime.timedelta(weeks=1)

    builder_2.button(text=_(buttons.prev_week),
                     callback_data=Schedule(action=Schedule.Action.week_details, date=prev_week.isoformat()))
    builder_2.button(text=_(buttons.next_week),
                     callback_data=Schedule(action=Schedule.Action.week_details, date=next_week.isoformat()))

    builder_2.button(
        text=_(buttons.schedule),
        callback_data=Schedule(action=Schedule.Action.show_week, date=date.isoformat())
    )

    builder_2.button(text=_(buttons.back), callback_data=Navigation(to=Navigation.To.schedule_menu))

    builder_2.adjust(1, 2, 1, 1)

    return builder_1.attach(builder_2).as_markup()


def get_homework_keyboard(lesson_id: int, date: datetime.date, homework: Homework | None, payload: Schedule.Action):
    if isinstance(date, datetime.datetime):
        date = date.date()

    iso_date = date.isoformat()

    builder = InlineKeyboardBuilder()

    if homework is None:
        builder.button(
            text=_(buttons.add),
            callback_data=Details(action=Details.Action.add, lesson_id=lesson_id, date=iso_date, payload=payload)
        )
    else:
        builder.button(
            text=_(buttons.edit),
            callback_data=Details(action=Details.Action.edit, lesson_id=lesson_id, date=iso_date, payload=payload)
        )
        builder.button(
            text=_(buttons.delete),
            callback_data=Details(action=Details.Action.delete, lesson_id=lesson_id, date=iso_date, payload=payload)
        )

    builder.button(text=_(buttons.back), callback_data=Schedule(action=payload, date=iso_date))

    builder.adjust(1)

    return builder.as_markup()


def get_week_schedule_keyboard(today: datetime.date, group_name):
    if isinstance(today, datetime.datetime):
        today = today.date()

    int_parity = 2 if not int(today.strftime('%V')) % 2 else 1

    today_iso = today.isoformat()
    next_week = (today + datetime.timedelta(weeks=1)).isoformat()
    prev_week = (today - datetime.timedelta(weeks=1)).isoformat()

    builder = InlineKeyboardBuilder()

    if int_parity == 1:
        builder.button(text=_(buttons.odd_week), callback_data='pass')
    else:
        builder.button(text=_(buttons.even_week), callback_data='pass')

    builder.button(text=_(buttons.prev_week), callback_data=Schedule(action=Schedule.Action.show_week, date=prev_week))
    builder.button(text=_(buttons.next_week), callback_data=Schedule(action=Schedule.Action.show_week, date=next_week))

    builder.button(text=_(buttons.details), callback_data=Schedule(action=Schedule.Action.week_details, date=today_iso))
    builder.button(
        text=_(buttons.group).format(group_name=group_name),
        callback_data=Navigation(to=Navigation.To.group_choose, payload=f'week_schedule;{today_iso}')
    )

    builder.button(text=_(buttons.back), callback_data=Navigation(to=Navigation.To.schedule_menu))

    builder.adjust(1, 2, 2, 1)

    return builder.as_markup()


def get_teachers_keyboard(group_name):
    builder = InlineKeyboardBuilder()

    builder.button(text=_(buttons.group).format(group_name=group_name),
                   callback_data=Navigation(to=Navigation.To.group_choose, payload='teachers'))
    builder.button(text=_(buttons.back), callback_data=Navigation.To.education)

    builder.adjust(1)

    return builder.as_markup()


def get_verification_keyboard(user: User, payload):
    is_verified = user.has_role(roles.verified)
    builder = InlineKeyboardBuilder()

    if not user.phone:
        builder.button(text=_(buttons.via_phone), callback_data=Action(name=Action.Name.send_phone, payload=payload))
    elif not is_verified:
        builder.button(text=_(buttons.check_phone), callback_data=Action(name=Action.Name.check_phone), payload=payload)
    
    if not (user.has_role(roles.authorized)):
        builder.button(text=_(buttons.kai_login),
                       callback_data=Action(name=Action.Name.start_kai_login, payload=payload))
    else:
        pass  # May be logout button
    
    if is_verified:
        builder.button(text=_(buttons.unlink_account),
                       callback_data=Action(name=Action.Name.unlink_account, payload=payload))
        
    if payload == 'at_start':
        builder.button(text=_(buttons.next_), callback_data=Navigation(to=Navigation.To.group_choose, payload=payload))
    else:
        builder.button(text=_(buttons.back), callback_data=Navigation(to=Navigation.To.profile, payload=payload))
    
    return builder.as_markup()


def get_cancel_keyboard(to: Cancel.To, payload=''):
    builder = InlineKeyboardBuilder()
    
    builder.button(text=_(buttons.cancel), callback_data=Cancel(to=to, payload=payload))
    
    return builder.as_markup()


def get_back_keyboard(to: Navigation.To, payload=''):
    builder = InlineKeyboardBuilder()
    
    builder.button(text=_(buttons.back), callback_data=Navigation(to=to, payload=payload))
    
    return builder.as_markup()


def get_channel_keyboard(channel_link):
    builder = InlineKeyboardBuilder()
    
    builder.button(text=_(buttons.channel), url=channel_link)
    
    return builder.as_markup()


def get_education_keyboard():
    builder = InlineKeyboardBuilder()
    
    builder.button(text=_(buttons.my_group), callback_data=Navigation(to=Navigation.To.my_group))
    builder.button(text=_(buttons.teachers), callback_data=Navigation(to=Navigation.To.teachers))
    
    builder.adjust(1)
    
    return builder.as_markup()


def get_my_group_keyboard(user: User):
    builder = InlineKeyboardBuilder()
    
    builder.button(text=_(buttons.classmates), callback_data=Navigation(to=Navigation.To.classmates))
    builder.button(text=_(buttons.documents), callback_data=Navigation(to=Navigation.To.documents))
    
    if user.has_right_to(rights.edit_group_pinned_message):
        builder.button(text=_(buttons.edit_pinned_text), callback_data=Action(name=Action.Name.edit_pinned_text))
    
    builder.button(text=_(buttons.back), callback_data=Navigation(to=Navigation.To.education))
    
    builder.adjust(1)
    
    return builder.as_markup()


def get_documents_keyboard():
    builder = InlineKeyboardBuilder()
    
    builder.button(text=_(buttons.educational_program),
                   callback_data=Action(name=Action.Name.send_document, payload='program'))
    builder.button(text=_(buttons.educational_program),
                   callback_data=Action(name=Action.Name.send_document, payload='syllabus'))
    builder.button(text=_(buttons.educational_program),
                   callback_data=Action(name=Action.Name.send_document, payload='schedule'))
    builder.button(text=_(buttons.back), callback_data=Navigation(to=Navigation.To.my_group))
    
    builder.adjust(1)
    
    return builder.as_markup()


def get_pin_text_keyboard():
    builder = InlineKeyboardBuilder()
    
    builder.button(text=_(buttons.clear), callback_data=Action(name=Action.Name.clear_pinned_text))
    builder.button(text=_(buttons.cancel), callback_data=Cancel(to=Cancel.To.my_group))
    
    builder.adjust(1)
    
    return builder.as_markup()


def get_help_keyboard(contact_url, channel_url, donate_url, guide_link):
    builder = InlineKeyboardBuilder()
    
    builder.button(text=_(buttons.contact_us), url=contact_url)
    builder.button(text=_(buttons.channel), url=channel_url)
    builder.button(text=_(buttons.support_project), url=donate_url)
    builder.button(text=_(buttons.guide), url=guide_link)
    
    builder.adjust(2, 1)
    
    return builder.as_markup()
