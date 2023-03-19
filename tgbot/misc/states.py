from aiogram.dispatcher.filters.state import StatesGroup, State


class ScheduleState(StatesGroup):
    today = State()


class GroupChoose(StatesGroup):
    waiting_for_group = State()


class KAILogin(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()
