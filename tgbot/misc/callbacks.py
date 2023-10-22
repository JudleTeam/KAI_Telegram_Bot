import datetime
from enum import Enum
from typing import Any

from aiogram.filters.callback_data import CallbackData


class Navigation(CallbackData, prefix='nav'):
    class To(str, Enum):
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
    class Name(str, Enum):
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
    class To(str, Enum):
        my_group = 'my_group'
        profile = 'profile'
        verification = 'verification'
        homework = 'homework'

    to: To
    payload: Any = None


class Language(CallbackData, prefix='lang'):
    code: str
    payload: Any = None


class Group(CallbackData, prefix='group'):
    class Action(str, Enum):
        select = 'select'
        add = 'add'
        remove = 'remove'

    action: Action
    id: int
    payload: Any = None


class Schedule(CallbackData, prefix='schedule'):
    class Action(str, Enum):
        day_details = 'day_details'
        week_details = 'week_details'
        show_day = 'show_day'
        show_week = 'show_week'

    action: Action
    date: str  # Date in ISO format or "today"/"tomorrow"/"after_tomorrow"


class FullSchedule(CallbackData, prefix='full_schedule'):
    parity: int

class Settings(CallbackData, prefix='settings'):
    class Action(str, Enum):
        emoji = 'emoji'
        teachers = 'teachers'

    action: Action


class Details(CallbackData, prefix='details'):
    class Action(str, Enum):
        show = 'show'
        add = 'add'
        edit = 'edit'
        delete = 'delete'

    action: Action
    lesson_id: int
    date: str  # Date in ISO format
    payload: Any = None
