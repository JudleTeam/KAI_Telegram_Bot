import logging

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

from tgbot.services.database.models import User
from tgbot.misc.texts import messages


class UserCheckerMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def on_pre_process_message(self, message: types.Message, data: dict):
        db_session = message.bot.get('database')
        redis = message.bot.get('redis')

        cached_is_user_exists = await redis.get(f'{message.from_id}:exists')
        cached_is_user_blocked = await redis.get(f'{message.from_id}:blocked')
        if cached_is_user_exists is None or cached_is_user_blocked is None:
            async with db_session() as session:
                database_user = await session.get(User, message.from_user.id)
                if database_user:
                    await redis.set(name=f'{message.from_id}:exists', value='1')
                    if database_user.is_blocked:
                        await redis.set(name=f'{message.from_id}:blocked', value='1')

                        await message.answer(messages.user_blocked)
                        raise CancelHandler()
                    else:
                        await redis.set(name=f'{message.from_id}:blocked', value='')
                else:
                    if message.text == '/start':
                        return

                    await redis.set(name=f'{message.from_id}:exists', value='')

                    logging.error(f'[{message.from_id}]: Unregistered')
                    await message.answer(messages.user_unregistered)
                    raise CancelHandler()
        else:
            if not cached_is_user_exists:
                if message.text == '/start':
                    return

                logging.error(f'[{message.from_id}]: Unregistered')
                await message.answer(messages.user_unregistered)
                raise CancelHandler()

            if cached_is_user_blocked:
                await message.answer(messages.user_blocked)
                raise CancelHandler()
