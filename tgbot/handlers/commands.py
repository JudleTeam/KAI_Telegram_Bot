from aiogram import Dispatcher
from aiogram.types import Message


async def command_start(message: Message):
    await message.reply('Hello, user!')


def register_commands(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'], state='*')
