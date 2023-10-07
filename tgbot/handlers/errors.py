from aiogram import Dispatcher
from aiogram.utils.exceptions import MessageNotModified, InvalidQueryID


async def handle_error(update, error):
    return True


def register_errors(dp: Dispatcher):
    dp.register_errors_handler(handle_error, exception=InvalidQueryID)
