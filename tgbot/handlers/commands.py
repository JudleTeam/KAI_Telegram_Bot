from aiogram import Dispatcher
from aiogram.types import Message

from tgbot.misc import messages
from tgbot.services.database.models import User


async def command_start(message: Message):
    db = message.bot.get('database')
    _ = message.bot.get('_')

    async with db.begin() as session:
        user = await session.get(User, message.from_id)
        if not user:
            redis = message.bot.get('redis')
            user = User(telegram_id=message.from_id, language_id=1, role_id=1)
            session.add(user)
            await redis.set(name=f'{message.from_id}:exists', value='1')


    await message.reply(_(messages.hello).format(name=message.from_user.first_name))


def register_commands(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'], state='*')
