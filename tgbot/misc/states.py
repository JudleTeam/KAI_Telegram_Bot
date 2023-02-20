from aiogram.dispatcher.filters.state import StatesGroup, State


class GroupChoose(StatesGroup):
    waiting_for_group = State()
