import logging

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import ContentType
from redis.asyncio import Redis

from tgbot.services.database.models import User
from tgbot.misc.texts import messages


class UserCheckerMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def on_pre_process_message(self, message: types.Message, data: dict):
        await self.check(message)

    async def on_pre_process_callback_query(self, call: types.CallbackQuery, data: dict):
        if 'start' in call.data:
            return

        await self.check(call.message)

    @staticmethod 
    async def check(message: types.Message):
        db_session = message.bot.get('database')
        redis: Redis = message.bot.get('redis')
        _ = message.bot.get('_')

        if message.chat.type != 'private' and message.content_type == ContentType.NEW_CHAT_MEMBERS:
            if any(message.bot.id == new_member.id for new_member in message.new_chat_members):
                await message.answer(_(messages.group_chat_error))
            raise CancelHandler()

        cached_is_user_exists = await redis.get(f'{message.chat.id}:exists')
        cached_is_user_blocked = await redis.get(f'{message.chat.id}:blocked')
        if cached_is_user_exists is None or cached_is_user_blocked is None:
            async with db_session() as session:
                database_user = await session.get(User, message.from_user.id)
                if database_user:
                    await redis.set(name=f'{message.chat.id}:exists', value='1', ex=3600)
                    if database_user.is_blocked:
                        await redis.set(name=f'{message.chat.id}:blocked', value='1', ex=3600)

                        await message.answer(_(messages.user_blocked))
                        raise CancelHandler()
                    else:
                        await redis.set(name=f'{message.chat.id}:blocked', value='', ex=3600)
                else:
                    if message.text == '/start':
                        return

                    await redis.set(name=f'{message.chat.id}:exists', value='', ex=3600)

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
