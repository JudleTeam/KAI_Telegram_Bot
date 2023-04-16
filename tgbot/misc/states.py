from aiogram.dispatcher.filters.state import StatesGroup, State


class ScheduleState(StatesGroup):
    today = State()


class GroupChoose(StatesGroup):
    waiting_for_group = State()


class KAILogin(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()


class GroupPinText(StatesGroup):
    waiting_for_text = State()


class PhoneSendState(StatesGroup):
    """
    State data:
    payload - Used to determine where verification occurs
    """
    waiting_for_phone = State()
