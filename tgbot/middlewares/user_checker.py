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

        database_user = None
        cached_is_user_exists = await redis.exists(f'{message.chat.id}:exists')
        if not cached_is_user_exists:
            if message.text == '/start':
                return

            async with db_session() as session:
                database_user = await session.get(User, message.from_user.id)

            if database_user is None:
                logging.error(f'[{message.chat.id}]: Unregistered')
                await message.answer(messages.user_unregistered)
                raise CancelHandler()

            await redis.set(name=f'{message.chat.id}:exists', value='', ex=3600)

        cached_is_user_blocked = await redis.exists(f'{message.chat.id}:blocked')
        if cached_is_user_blocked:
            await message.answer(_(messages.user_blocked))
            raise CancelHandler()

        if database_user is None:
            async with db_session() as session:
                database_user = await session.get(User, message.from_user.id)

        if database_user.is_blocked:
            await redis.set(name=f'{message.chat.id}:blocked', value='', ex=3600)
            await message.answer(_(messages.user_blocked))
            raise CancelHandler()
