from aiogram import Dispatcher
from aiogram.types import Message

from tgbot.misc import messages


async def command_start(message: Message):
    _ = message.bot.get('_')

    await message.reply(_(messages.hello).format(name=message.from_user.first_name))


def register_commands(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'], state='*')
