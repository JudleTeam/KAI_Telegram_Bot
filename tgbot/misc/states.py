from aiogram.dispatcher.filters.state import StatesGroup, State


class ScheduleState(StatesGroup):
    today = State()
