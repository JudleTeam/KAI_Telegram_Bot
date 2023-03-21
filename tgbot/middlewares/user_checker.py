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
        await self.check(message)

    async def on_pre_process_callback_query(self, call: types.CallbackQuery, data: dict):
        await self.check(call.message)

    @staticmethod 
    async def check(message: types.Message):
        db_session = message.bot.get('database')
        redis = message.bot.get('redis')
        _ = message.bot.get('_')

        if message.chat.type != 'private':
            await message.answer(_(messages.group_chat_error))
            raise CancelHandler()

        cached_is_user_exists = await redis.get(f'{message.chat.id}:exists')
        cached_is_user_blocked = await redis.get(f'{message.chat.id}:blocked')
        if cached_is_user_exists is None or cached_is_user_blocked is None:
            async with db_session() as session:
                database_user = await session.get(User, message.from_user.id)
                if database_user:
                    await redis.set(name=f'{message.chat.id}:exists', value='1')
                    if database_user.is_blocked:
                        await redis.set(name=f'{message.chat.id}:blocked', value='1')

                        await message.answer(_(messages.user_blocked))
                        raise CancelHandler()
                    else:
                        await redis.set(name=f'{message.chat.id}:blocked', value='')
                else:
                    if message.text == '/start':
                        return

                    await redis.set(name=f'{message.chat.id}:exists', value='')

                    logging.error(f'[{message.chat.id}]: Unregistered')
                    await message.answer(messages.user_unregistered)
                    raise CancelHandler()
        else:
            if not cached_is_user_exists:
                if message.text == '/start':
                    return

                logging.error(f'[{message.chat.id}]: Unregistered')
                await message.answer(messages.user_unregistered)
                raise CancelHandler()

            if cached_is_user_blocked:
                await message.answer(_(messages.user_blocked))
                raise CancelHandler()
