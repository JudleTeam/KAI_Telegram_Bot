import datetime
from enum import Enum
from typing import Any

from aiogram.filters.callback_data import CallbackData


class Navigation(CallbackData, prefix='nav'):
    class To(Enum, str):
        my_group = 'my_group'
        group_choose = 'group_choose'
        profile = 'profile'
        education = 'education'
        main_menu = 'main_menu'
        classmates = 'classmates'
        documents = 'documents'
        verification = 'verification'
        settings = 'settings'
        schedule_menu = 'schedule_menu'
        teachers = 'teachers'
        language_choose = 'language_choose'

    to: To
    payload: Any = None


class Action(CallbackData, prefix='act'):
    class Name(Enum, str):
        edit_pinned_text = 'edit_pin_text'
        clear_pinned_text = 'clear_pin_text'
        send_document = 'send_doc'
        start_kai_login = 'start_kai_login'
        kai_logout = 'kai_logout'
        unlink_account = 'unlink_account'
        send_phone = 'send_phone'
        check_phone = 'check_phone'

    name: Name
    payload: Any = None


class Cancel(CallbackData, prefix='cancel'):
    class To(Enum, str):
        pass

    to: To
    payload: Any = None


class Language(CallbackData, prefix='lang'):
    lang_id: int
    code: str
    payload: Any = None


class Group(CallbackData, prefix='group'):
    class Action(Enum, str):
        select = 'select'
        add = 'add'
        remove = 'remove'

    id: int
    payload: Any = None


class Schedule(CallbackData, prefix='schedule'):
    class Action(Enum, str):
        day_details = 'day_details'
        week_details = 'week_details'
        show_day = 'show_day'
        show_week = 'show_week'

    payload: Any = None


class FullSchedule(CallbackData, prefix='full_schedule'):
    parity: int

class Settings(CallbackData, prefix='settings'):
    class Action(Enum, str):
        emoji = 'emoji'
        teachers = 'teachers'

    action: Action


class Details(CallbackData, prefix='details'):
    class Action(Enum, str):
        show = 'show'
        add = 'add'
        edit = 'edit'
        delete = 'delete'

    lesson_id: int
    date: datetime.date
    payload: Any = None
