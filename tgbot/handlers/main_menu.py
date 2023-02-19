from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import Message

from tgbot.misc.texts import reply_commands, messages


async def send_schedule_menu(message: Message):
    await message.answer(messages.schedule_menu)


async def send_profile_menu(message: Message):
    await message.answer(messages.profile_menu)


async def send_shop_menu(message: Message):
    await message.answer(messages.in_development)


async def send_education_menu(message: Message):
    await message.answer(messages.in_development)


def register_main_menu(dp: Dispatcher):
    dp.register_message_handler(send_schedule_menu, Text(startswith=reply_commands.schedule_symbol))
    dp.register_message_handler(send_profile_menu, Text(startswith=reply_commands.profile_symbol))
    dp.register_message_handler(send_shop_menu, Text(startswith=reply_commands.shop_symbol))
    dp.register_message_handler(send_education_menu, Text(startswith=reply_commands.education_symbol))
